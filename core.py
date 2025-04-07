import logging
from user_manager import UserManager
from exchange_pool import ExchangePool
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from market_state_analyzer import analyze_market_state

logging.basicConfig(
    level=logging.INFO,
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
        users = await user_manager.get_users()
        logger.info(f"Loaded {len(users)} users from Redis: {users}")

        for user, credentials in users.items():
            logger.info(f"Processing symbols for user {user} with credentials: {credentials}")
            async with ExchangePool(credentials['api_key'], credentials['api_secret'], user) as exchange:
                logger.debug(f"Exchange object: {exchange}")
                # Анализируем состояние рынка
                market_state = await analyze_market_state(exchange, timeframe)
                logger.info(f"Market state for user {user}: {market_state}")
                valid_symbols = await filter_symbols(exchange, exchange.symbols, since, limit, timeframe, user, market_state)
                logger.info(f"Filtered symbols for user {user}: {valid_symbols}")
                await start_trading_all(exchange, valid_symbols, user)
            logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols")
    except Exception as e:
        logger.error(f"Error in main: {type(e).__name__}: {str(e)}")
    finally:
        await user_manager.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
