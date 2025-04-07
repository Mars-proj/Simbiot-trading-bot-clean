# core.py
import logging
from user_manager import UserManager
from exchange_pool import ExchangePool
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from market_state_analyzer import analyze_market_state
import asyncio
import concurrent.futures
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('main')

async def process_user(user, credentials, since, limit, timeframe):
    """Обрабатывает одного пользователя."""
    try:
        logger.info(f"Processing symbols for user {user} with credentials: {credentials}")
        exchange_pool = ExchangePool(credentials['api_key'], credentials['api_secret'], user)
        async with exchange_pool as exchange:
            logger.debug(f"Exchange object created for user {user}: {exchange}")
            # Анализируем состояние рынка
            logger.debug(f"Calling analyze_market_state for user {user}")
            market_state, symbols = await analyze_market_state(exchange_pool, timeframe)
            logger.info(f"Market state for user {user}: {market_state}")
            # Если market_state дефолтный, всё равно продолжаем
            if market_state['trend'] == 'neutral' and market_state['volatility'] == 0.01:
                logger.warning(f"Using default market state for user {user} due to analysis failure")
            # Используем символы, возвращённые из analyze_market_state
            if not symbols:
                logger.error(f"No symbols available for user {user}, skipping")
                return
            logger.debug(f"Calling filter_symbols for user {user} with {len(symbols)} symbols")
            valid_symbols = await filter_symbols(exchange_pool, symbols, since, limit, timeframe, user, market_state)
            logger.info(f"Filtered symbols for user {user}: {valid_symbols}")
            logger.debug(f"Calling start_trading_all for user {user}")
            await start_trading_all(exchange, valid_symbols, user)
            logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols")
    except Exception as e:
        logger.error(f"Error processing user {user}: {type(e).__name__}: {str(e)}")

async def main():
    user_manager = UserManager()
    # Устанавливаем since на 1 месяц назад от текущей даты
    current_timestamp = int(datetime.now().timestamp() * 1000)  # Текущий timestamp в миллисекундах
    since = current_timestamp - (30 * 24 * 60 * 60 * 1000)  # 30 дней назад
    limit = 1000
    timeframe = '4h'  # Изменяем таймфрейм на 4h

    try:
        logger.debug("Loading users from Redis")
        users = await user_manager.get_users()
        logger.info(f"Loaded {len(users)} users from Redis: {users}")

        # Создаём пул задач для параллельной обработки пользователей
        tasks = []
        for user, credentials in users.items():
            tasks.append(process_user(user, credentials, since, limit, timeframe))

        # Ограничиваем количество одновременно выполняемых задач (например, 100)
        # Это позволяет масштабировать систему для 1000+ пользователей
        max_concurrent_tasks = 100
        for i in range(0, len(tasks), max_concurrent_tasks):
            batch = tasks[i:i + max_concurrent_tasks]
            await asyncio.gather(*batch, return_exceptions=True)
            logger.info(f"Processed batch of {len(batch)} users")

    except Exception as e:
        logger.error(f"Error in main: {type(e).__name__}: {str(e)}")
    finally:
        logger.debug("Closing user manager")
        await user_manager.close()

if __name__ == "__main__":
    logger.debug("Starting main execution")
    asyncio.run(main())
