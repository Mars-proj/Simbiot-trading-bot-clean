import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)

class ExchangePool:
    def __init__(self):
        self.exchanges = {}

    async def add_exchange(self, exchange_id, api_key, api_secret):
        """
        Add an exchange to the pool.

        Args:
            exchange_id: ID of the exchange (e.g., 'binance').
            api_key: API key for the exchange.
            api_secret: API secret for the exchange.

        Returns:
            Exchange instance.
        """
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            await exchange.load_markets()
            self.exchanges[exchange_id] = exchange
            logger.info(f"Added exchange {exchange_id} to pool")
            return exchange
        except Exception as e:
            logger.error(f"Failed to add exchange {exchange_id}: {str(e)}")
            raise

    async def get_exchange(self, exchange_id):
        """
        Get an exchange from the pool.

        Args:
            exchange_id: ID of the exchange.

        Returns:
            Exchange instance.
        """
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not found in pool")
        return self.exchanges[exchange_id]

    async def close(self):
        """
        Close all exchanges in the pool.
        """
        for exchange_id, exchange in self.exchanges.items():
            await exchange.close()
            logger.info(f"Closed exchange {exchange_id}")
        self.exchanges.clear()
