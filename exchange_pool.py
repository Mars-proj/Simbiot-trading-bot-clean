from logging_setup import logger_main
from exchange_factory import create_exchange

class ExchangePool:
    def __init__(self):
        self.exchanges = {}

    async def get_exchange(self, exchange_id, user_id, testnet=False):
        """Gets or creates an exchange instance for the user."""
        try:
            key = f"{exchange_id}:{user_id}"
            if key not in self.exchanges:
                exchange = create_exchange(exchange_id, user_id, testnet)
                self.exchanges[key] = exchange
                logger_main.info(f"Created new exchange instance for {key}")
            return self.exchanges[key]
        except Exception as e:
            logger_main.error(f"Error getting exchange for {exchange_id}:{user_id}: {e}")
            return None

    async def close_all(self):
        """Closes all exchange instances."""
        for key, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger_main.info(f"Closed exchange connection for {key}")
            except Exception as e:
                logger_main.error(f"Error closing exchange for {key}: {e}")
        self.exchanges.clear()

__all__ = ['ExchangePool']
