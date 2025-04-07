import logging
from user_manager import UserManager
from exchange_pool import ExchangePool
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all

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
        logger.info(f"Loaded {len(users)} users from Redis")

        for user, credentials in users.items():
            logger.info(f"Processing symbols for user {user}")
            async with ExchangePool(credentials['api_key'], credentials['api_secret'], user) as exchange:
                valid_symbols = await filter_symbols(exchange, exchange.symbols, since, limit, timeframe, user)
                await start_trading_all(exchange, valid_symbols, user)
            logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await user_manager.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
