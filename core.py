import logging
import asyncio
import sys
import os
import ccxt.async_support as ccxt
import time
from user_manager import UserManager
from market_state_analyzer import analyze_market_state
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from celery_app import process_user_task
from exchange_pool import ExchangePool
from exchange_factory import ExchangeFactory
from exchange_detector import ExchangeDetector
from monitoring import start_monitoring, record_trade, update_balance

logger = logging.getLogger("main")

async def check_user_balance(exchange, user, min_balance=10.0):
    """
    Check if the user has sufficient USDT balance for trading.

    Args:
        exchange: Exchange instance.
        user: User identifier.
        min_balance: Minimum required USDT balance (default: 10.0).

    Returns:
        bool: True if balance is sufficient, False otherwise.
    """
    try:
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        logger.debug(f"User {user} balance: {usdt_balance} USDT")
        update_balance(user, usdt_balance)  # Обновляем метрику в Prometheus
        if usdt_balance < min_balance:
            logger.warning(f"User {user} has insufficient balance ({usdt_balance} USDT), skipping trading...")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to check balance for {user}: {type(e).__name__}: {str(e)}")
        return False

async def process_user(user, credentials, since, limit, timeframe, symbol_batch, exchange_pool, detector):
    """
    Process trading for a user with a batch of symbols.

    Args:
        user: User identifier.
        credentials: User's API credentials (dict with 'api_key' and 'api_secret').
        since: Timestamp to fetch OHLCV data from (in milliseconds).
        limit: Number of OHLCV candles to fetch.
        timeframe: Timeframe for OHLCV data (e.g., '1h').
        symbol_batch: List of symbols to process.
        exchange_pool: ExchangePool instance.
        detector: ExchangeDetector instance.
    """
    try:
        exchange_name, exchange = await detector.detect_exchange(credentials['api_key'], credentials['api_secret'])
        exchange = exchange_pool.get_exchange(exchange_name, credentials)
    except Exception as e:
        logger.error(f"Failed to detect exchange for user {user}: {type(e).__name__}: {str(e)}")
        return

    try:
        if not await check_user_balance(exchange, user):
            return

        await exchange.load_markets()
        market_state = await analyze_market_state(exchange, "BTC/USDT")
        signal_count = await start_trading_all(exchange, symbol_batch, user, market_state)
        record_trade(user)  # Записываем торговлю в Prometheus
        logger.info(f"Processed {signal_count} signals for user {user} with batch {symbol_batch}")
    except Exception as e:
        logger.error(f"Failed to process user {user}: {type(e).__name__}: {str(e)}")

async def main():
    """
    Main execution loop for the trading bot.

    - Loads users from PostgreSQL.
    - Filters symbols for each user.
    - Distributes trading tasks to Celery workers.
    - Runs in an infinite loop with a dynamic interval.
    """
    logger.debug("Starting main execution")
    start_monitoring()  # Запускаем Prometheus
    exchange_pool = ExchangePool()
    detector = ExchangeDetector()
    async with UserManager() as user_manager:
        # Добавляем пользователя с предоставленными ключами
        user_id = "main_user"
        api_key = "mx0vglM30RTqlJzTGF"
        api_secret = "74320c83880348768a6b68973d50854b"
        try:
            await user_manager.add_user(user_id, api_key, api_secret)
            logger.info(f"Added user {user_id} with provided API keys")
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {type(e).__name__}: {str(e)}")
            return

        cycle = 1
        since = int(time.time() * 1000) - 2_592_000_000  # 30 дней назад
        limit = 50
        timeframe = '4h'
        batch_size = 500
        while True:
            start_time = time.time()
            logger.info(f"Starting cycle {cycle}")
            users = await user_manager.get_users()
            logger.info(f"Loaded {len(users)} users from PostgreSQL: {users}")
            tasks = []
            for user, credentials in users.items():
                try:
                    all_symbols = list(exchange_pool.get_exchange("mexc", credentials).markets.keys())
                    valid_symbols = await filter_symbols(exchange_pool.get_exchange("mexc", credentials), all_symbols, since, limit, timeframe, user=user, batch_size=batch_size)
                except Exception as e:
                    logger.error(f"Failed to load symbols for user {user}: {type(e).__name__}: {str(e)}")
                    continue

                for i in range(0, len(valid_symbols), batch_size):
                    symbol_batch = valid_symbols[i:i + batch_size]
                    try:
                        task = process_user_task.delay(user, credentials, since, limit, timeframe, symbol_batch, exchange_pool, detector)
                        tasks.append(task)
                    except Exception as e:
                        logger.error(f"Failed to submit task for user {user}: {type(e).__name__}: {str(e)}")
                        if "ConnectionError" in str(e) or "TimeoutError" in str(e):
                            logger.warning("RabbitMQ connection issue detected, retrying in 60 seconds...")
                            await asyncio.sleep(60)
                            continue

            if tasks:
                for task in tasks:
                    try:
                        while not task.ready():
                            await asyncio.sleep(1)
                        if task.successful():
                            logger.debug(f"Task {task.id} completed successfully")
                        else:
                            logger.error(f"Task {task.id} failed: {task.get(propagate=False)}")
                    except Exception as e:
                        logger.error(f"Error waiting for task {task.id}: {type(e).__name__}: {str(e)}")
                        if "ConnectionError" in str(e) or "TimeoutError" in str(e):
                            logger.warning("RabbitMQ connection issue detected, retrying in 60 seconds...")
                            await asyncio.sleep(60)
            else:
                logger.warning("No tasks to process in this cycle")

            logger.info(f"Completed cycle {cycle}")
            cycle += 1
            elapsed_time = time.time() - start_time
            logger.info(f"Cycle {cycle-1} took {elapsed_time:.2f} seconds")
            sleep_time = max(120 - elapsed_time, 0)  # Динамический интервал
            await asyncio.sleep(sleep_time)

    await exchange_pool.close_all()

if __name__ == "__main__":
    from logging_setup import setup_logging
    setup_logging()
    asyncio.run(main())
