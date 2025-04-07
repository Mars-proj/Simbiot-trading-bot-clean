import logging
from user_manager import UserManager
from exchange_pool import ExchangePool
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from market_state_analyzer import analyze_market_state
import asyncio

logging.basicConfig(
    level=logging.DEBUG,  # Увеличиваем уровень логирования до DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('main')

async def main():
    user_manager = UserManager()
    since = 1736219256  # Example timestamp
    limit = 2000
    timeframe = '1h'

    try:
        logger.debug("Loading users from Redis")
        users = await user_manager.get_users()
        logger.info(f"Loaded {len(users)} users from Redis: {users}")

        for user, credentials in users.items():
            logger.info(f"Processing symbols for user {user} with credentials: {credentials}")
            async with ExchangePool(credentials['api_key'], credentials['api_secret'], user) as exchange:
                logger.debug(f"Exchange object created: {exchange}")
                # Анализируем состояние рынка
                logger.debug(f"Calling analyze_market_state for user {user}")
                market_state, symbols = await analyze_market_state(exchange, timeframe)
                logger.info(f"Market state for user {user}: {market_state}")
                # Если market_state дефолтный, всё равно продолжаем
                if market_state['trend'] == 'neutral' and market_state['volatility'] == 0.01:
                    logger.warning(f"Using default market state for user {user} due to analysis failure")
                # Используем символы, возвращённые из analyze_market_state
                if not symbols:
                    logger.error(f"No symbols available for user {user}, skipping")
                    continue
                logger.debug(f"Calling filter_symbols for user {user} with {len(symbols)} symbols")
                valid_symbols = await filter_symbols(exchange, symbols, since, limit, timeframe, user, market_state)
                logger.info(f"Filtered symbols for user {user}: {valid_symbols}")
                logger.debug(f"Calling start_trading_all for user {user}")
                await start_trading_all(exchange, valid_symbols, user)
            logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols")
    except Exception as e:
        logger.error(f"Error in main: {type(e).__name__}: {str(e)}")
    finally:
        logger.debug("Closing user manager")
        await user_manager.close()

if __name__ == "__main__":
    logger.debug("Starting main execution")
    asyncio.run(main())
