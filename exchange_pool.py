from logging_setup import logger_main
from exchange_factory import create_exchange  # Импортируем функцию create_exchange напрямую

class ExchangePool:
    def __init__(self):
        self.exchanges = {}
        logger_main.info("Initialized ExchangePool")

    async def get_exchange(self, exchange_id, user_id, testnet=False):
        key = f"{exchange_id}:{user_id}"
        logger_main.info(f"Getting exchange for {key} (testnet: {testnet})")
        if key in self.exchanges:
            logger_main.info(f"Returning cached exchange for {key}")
            return self.exchanges[key]
        try:
            logger_main.info(f"Creating new exchange instance for {key}")
            exchange = create_exchange(exchange_id, user_id, testnet)  # Используем функцию create_exchange
            if exchange is None:
                logger_main.error(f"create_exchange returned None for {key}")
                return None
            self.exchanges[key] = exchange
            logger_main.info(f"Created new exchange instance for {key}")
            return exchange
        except Exception as e:
            logger_main.error(f"Failed to create exchange instance for {key}: {e}")
            return None

    async def close_all(self):
        logger_main.info("Closing all exchange instances")
        for key, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger_main.info(f"Closed exchange instance for {key}")
            except Exception as e:
                logger_main.error(f"Failed to close exchange instance for {key}: {e}")
        self.exchanges.clear()
        logger_main.info("All exchange instances closed")
