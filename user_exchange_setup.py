import asyncio
from trade_executor_core import TradeExecutor
from config import API_KEYS, PREFERRED_EXCHANGES
from utils import logger_main, log_exception
from exchange_utils import invalid_api_users, unavailable_symbols, filtered_symbols_cache, symbol_check_cache, semaphore, REQUEST_DELAY
from async_exchange_fetcher import async_exchange_fetcher
from exchange_factory import create_exchange
from symbol_filtering import filter_symbols_for_exchange

async def setup_exchange(user_id, user_data, preferred_exchange, loop=None):
    """Sets up an exchange for a single user with rate limiting"""
    async with semaphore:
        logger_main.debug(f"Setting up exchange {preferred_exchange} for user {user_id}")
        try:
            if preferred_exchange not in user_data:
                logger_main.error(f"Data for {preferred_exchange} missing in user_data for {user_id}: {user_data}")
                invalid_api_users.add(user_id)
                return None
            exchange_data = user_data[preferred_exchange]
            required_keys = ['api_key', 'api_secret']
            for key in required_keys:
                if key not in exchange_data:
                    logger_main.error(f"Key {key} missing in data for {preferred_exchange} for {user_id}: {exchange_data}")
                    invalid_api_users.add(user_id)
                    return None
            exchange = await create_exchange(preferred_exchange, exchange_data, loop)
            if exchange is None:
                invalid_api_users.add(user_id)
                return None
            logger_main.debug(f"Synchronizing time with {preferred_exchange} server for {user_id}")
            try:
                await asyncio.wait_for(async_exchange_fetcher.fetch_time(exchange), timeout=10)
                logger_main.debug(f"Time successfully synchronized with {preferred_exchange} server")
            except asyncio.TimeoutError as e:
                logger_main.error(f"Timeout synchronizing time with {preferred_exchange} server for {user_id}: {str(e)}")
                log_exception(f"Timeout synchronizing time: {str(e)}", e)
                invalid_api_users.add(user_id)
                return None
            except Exception as e:
                logger_main.error(f"Error synchronizing time with {preferred_exchange} server for {user_id}: {str(e)}")
                log_exception(f"Error synchronizing time: {str(e)}", e)
                invalid_api_users.add(user_id)
                return None
            logger_main.debug(f"Created {preferred_exchange} object for {user_id}, loading markets")
            for attempt in range(3):
                try:
                    await asyncio.wait_for(async_exchange_fetcher.load_markets(exchange), timeout=60)
                    logger_main.debug(f"Markets successfully loaded for {preferred_exchange} for {user_id}")
                    break
                except asyncio.TimeoutError as e:
                    logger_main.warning(f"Timeout loading markets for {preferred_exchange} for {user_id} (attempt {attempt + 1}/3): {str(e)}")
                    if attempt == 2:
                        logger_main.error(f"Failed to load markets after 3 attempts for {preferred_exchange} for {user_id}: {str(e)}")
                        log_exception(f"Timeout loading markets: {str(e)}", e)
                        invalid_api_users.add(user_id)
                        return None
                    await asyncio.sleep(5)
                except ccxt.AuthenticationError as e:
                    logger_main.error(f"Authentication error for {user_id} on {preferred_exchange}: {str(e)}")
                    invalid_api_users.add(user_id)
                    return None
                except ccxt.BadRequest as e:
                    logger_main.error(f"Invalid API key for {user_id} on {preferred_exchange}: {str(e)}")
                    invalid_api_users.add(user_id)
                    return None
                except Exception as e:
                    logger_main.error(f"Unknown error loading markets for {preferred_exchange} for {user_id}: {str(e)}")
                    log_exception(f"Error loading markets: {str(e)}", e)
                    invalid_api_users.add(user_id)
                    return None
            if preferred_exchange not in unavailable_symbols:
                unavailable_symbols[preferred_exchange] = set()
            logger_main.debug(f"Unavailable symbols for {preferred_exchange}: {unavailable_symbols[preferred_exchange]}")
            trade_executor = TradeExecutor()
            logger_main.debug(f"Initializing deposit for {user_id} on {preferred_exchange}")
            await trade_executor.initialize_deposit(exchange, user_id)
            logger_main.debug(f"Deposit successfully initialized for {user_id} on {preferred_exchange}")
            logger_main.debug(f"Exchange {preferred_exchange} for user {user_id} successfully set up")
            # Dynamic request delay based on number of users
            delay = REQUEST_DELAY * (1 + len(API_KEYS) / 10)  # Increase delay with more users
            await asyncio.sleep(delay)
            return (user_id, preferred_exchange, exchange, trade_executor)
        except Exception as e:
            logger_main.error(f"Error setting up exchange {preferred_exchange} for user {user_id}: {str(e)}")
            log_exception(f"Error setting up exchange: {str(e)}", e)
            invalid_api_users.add(user_id)
            return None

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
        # Set up exchanges for each user
        tasks = []
        for user_id, user_data in users.items():
            preferred_exchange = PREFERRED_EXCHANGES.get(user_id)
            if not preferred_exchange:
                logger_main.warning(f"Preferred exchange for {user_id} not specified, skipping")
                continue
            logger_main.debug(f"Adding task to set up {preferred_exchange} for {user_id}")
            task = setup_exchange(user_id,
