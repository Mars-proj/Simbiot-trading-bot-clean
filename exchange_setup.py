import asyncio
from config import API_KEYS, PREFERRED_EXCHANGES
from utils import logger_main, log_exception
from exchange_utils import invalid_api_users, filtered_symbols_cache
from exchange_setup_utils import create_exchange
from exchange_symbol_filter import filter_symbols_for_exchange
from exchange_user_setup import setup_exchange

async def setup_exchanges(loop=None, market_conditions=None):
    """Sets up exchanges for all users"""
    exchanges = {}
    try:
        logger_main.debug("Starting exchange setup")
        users = API_KEYS
        logger_main.info(f"Found {len(users)} users to set up")
        logger_main.debug(f"API_KEYS content: {API_KEYS}")
        logger_main.debug(f"PREFERRED_EXCHANGES content: {PREFERRED_EXCHANGES}")
        # Filter symbols for each unique exchange using the first user's API key
        unique_exchanges = set(PREFERRED_EXCHANGES.values())
        for preferred_exchange in unique_exchanges:
            if preferred_exchange in filtered_symbols_cache:
                logger_main.debug(f"Symbols for {preferred_exchange} already in cache, skipping filtration")
                continue
            # Find the first user for this exchange
            user_id = next((user_id for user_id, data in users.items() if PREFERRED_EXCHANGES[user_id] == preferred_exchange), None)
            if not user_id:
                logger_main.warning(f"No users found for exchange {preferred_exchange}, skipping")
                continue
            exchange_data = users[user_id].get(preferred_exchange)
            if not exchange_data:
                logger_main.error(f"No exchange data for {preferred_exchange} for user {user_id}")
                continue
            filtered_symbols = await filter_symbols_for_exchange(preferred_exchange, exchange_data, loop)
            if not filtered_symbols:
                logger_main.warning(f"No symbols filtered for {preferred_exchange}, skipping")
                continue
            filtered_symbols_cache[preferred_exchange] = filtered_symbols
        # Set up exchanges for each user
        tasks = []
        for user_id, user_data in users.items():
            preferred_exchange = PREFERRED_EXCHANGES.get(user_id)
            if not preferred_exchange:
                logger_main.warning(f"Preferred exchange for {user_id} not specified, skipping")
                continue
            logger_main.debug(f"Adding task to set up {preferred_exchange} for {user_id}")
            task = setup_exchange(user_id, user_data, preferred_exchange, loop=loop)
            tasks.append(task)
        if not tasks:
            logger_main.error("No tasks to set up exchanges, API_KEYS or PREFERRED_EXCHANGES is empty")
            return {}
        logger_main.debug(f"Running {len(tasks)} tasks to set up exchanges")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if result is None or isinstance(result, Exception):
                logger_main.warning(f"Exchange setup result: {result}")
                continue
            user_id, preferred_exchange, exchange, trade_executor = result
            exchanges[(user_id, preferred_exchange)] = (exchange, trade_executor)
            logger_main.debug(f"Exchange for {user_id} on {preferred_exchange} successfully set up")
        logger_main.info(f"Exchange setup completed: {len(exchanges)} exchanges set up")
        if not exchanges:
            logger_main.error("Failed to set up any exchanges, check API keys and configuration")
        return exchanges
    except Exception as e:
        logger_main.error(f"Error in setup_exchanges: {str(e)}")
        log_exception(f"Error in setup_exchanges: {str(e)}", e)
        return {}

__all__ = ['setup_exchanges']
