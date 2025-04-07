import logging
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
    users = {
        'user1': {'api_key': 'your_api_key_1', 'api_secret': 'your_api_secret_1'},
        'user2': {'api_key': 'your_api_key_2', 'api_secret': 'your_api_secret_2'},
        'user3': {'api_key': 'your_api_key_3', 'api_secret': 'your_api_secret_3'}
    }
    since = 1736219256  # Example timestamp
    limit = 2000
    timeframe = '1h'

    for user, credentials in users.items():
        logger.info(f"Processing symbols for user {user}")
        async with ExchangePool(credentials['api_key'], credentials['api_secret']) as exchange:
            valid_symbols = await filter_symbols(exchange, exchange.symbols, since, limit, timeframe, user)
            await start_trading_all(exchange, valid_symbols, user)  # Исправлено: убрали since
        logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
