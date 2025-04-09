# core.py
import logging
import asyncio
import sys
import os
import ccxt.async_support as ccxt
from user_manager import UserManager
from market_state_analyzer import analyze_market_state
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from celery_app import process_user_task

# Добавляем текущую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("main")

async def check_user_balance(exchange, user, min_balance=10.0):
    """Проверяет баланс пользователя и возвращает True, если достаточно средств."""
    try:
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        logger.debug(f"User {user} balance: {usdt_balance} USDT")
        if usdt_balance < min_balance:
            logger.warning(f"User {user} has insufficient balance ({usdt_balance} USDT), skipping trading...")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to check balance for {user}: {type(e).__name__}: {str(e)}")
        return False

async def process_user(user, credentials, since, limit, timeframe, symbol_batch):
    exchange = ccxt.mexc({
        'apiKey': credentials['api_key'],
        'secret': credentials['api_secret'],
        'enableRateLimit': True,
    })
    try:
        # Проверяем баланс пользователя
        if not await check_user_balance(exchange, user):
            return

        await exchange.load_markets()
        market_state = await analyze_market_state(exchange, "BTC/USDT")
        signal_count = await start_trading_all(exchange, symbol_batch, user, market_state)
        logger.info(f"Processed {signal_count} signals for user {user} with batch {symbol_batch}")
    except Exception as e:
        logger.error(f"Failed to process user {user}: {type(e).__name__}: {str(e)}")
    finally:
        await exchange.close()

async def main():
    logger.debug("Starting main execution")
    async with UserManager() as user_manager:
        cycle = 1
        since = 1000
        limit = 100
        timeframe = '4h'
        batch_size = 500  # Размер батча для фильтрации символов
        while True:
            logger.info(f"Starting cycle {cycle}")
            users = await user_manager.get_users()
            logger.info(f"Loaded {len(users)} users from Redis: {users}")
            tasks = []
            for user, credentials in users.items():
                exchange = None
                try:
                    # Загружаем все символы
                    exchange = ccxt.mexc({
                        'apiKey': credentials['api_key'],
                        'secret': credentials['api_secret'],
                        'enableRateLimit': True,
                    })
                    await exchange.load_markets()
                    all_symbols = list(exchange.markets.keys())
                    # Фильтруем символы по батчам
                    valid_symbols = await filter_symbols(exchange, all_symbols, since, limit, timeframe, user=user, batch_size=batch_size)
                except Exception as e:
                    logger.error(f"Failed to load symbols for user {user}: {type(e).__name__}: {str(e)}")
                    continue
                finally:
                    if exchange:
                        await exchange.close()

                # Разделяем валидные символы на батчи по 500 для торговли
                for i in range(0, len(valid_symbols), batch_size):
                    symbol_batch = valid_symbols[i:i + batch_size]
                    task = process_user_task.delay(user, credentials, since, limit, timeframe, symbol_batch)
                    tasks.append(task)

            for task in tasks:
                await task.wait()
            logger.info(f"Completed cycle {cycle}")
            cycle += 1
            await asyncio.sleep(120)  # Цикл каждые 2 минуты

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
