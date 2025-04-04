# exchange_pool.py
import ccxt.async_support as ccxt
from logging_setup import logger_main
from config_keys import API_KEYS  # Исправляем импорт на API_KEYS

class ExchangePool:
    def __init__(self):
        logger_main.info("Initialized ExchangePool")
        self.exchanges = {}

    async def get_exchange(self, exchange_id, user_id, testnet=False):
        logger_main.info(f"Getting exchange for {exchange_id}:{user_id} (testnet: {testnet})")
        key = f"{exchange_id}:{user_id}"
        if key in self.exchanges:
            return self.exchanges[key]

        logger_main.info(f"Creating new exchange instance for {exchange_id}:{user_id}")
        # Validate API keys
        if user_id not in API_KEYS or exchange_id not in API_KEYS[user_id]:
            logger_main.error(f"No API keys found for user {user_id} on {exchange_id}")
            return None

        api_key = API_KEYS[user_id][exchange_id]["api_key"]
        api_secret = API_KEYS[user_id][exchange_id]["api_secret"]
        logger_main.info("API keys validated successfully")

        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        if testnet:
            exchange.set_sandbox_mode(True)

        logger_main.info(f"Created exchange instance for {exchange_id} (user: {user_id}, testnet: {testnet}) with rateLimit: {exchange.rateLimit}")
        self.exchanges[key] = exchange
        return exchange

    async def close_all(self):
        logger_main.info("Closing all exchange instances in ExchangePool")
        for key, exchange in self.exchanges.items():
            try:
                await exchange.close()  # Закрываем соединение
                logger_main.info(f"Closed exchange instance for {key}")
            except Exception as e:
                logger_main.error(f"Error closing exchange instance for {key}: {e}")
        self.exchanges.clear()
