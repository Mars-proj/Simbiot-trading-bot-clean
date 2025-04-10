import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)

class ExchangeDetector:
    def __init__(self):
        self.exchanges = {}

    async def detect_exchange(self, api_key, api_secret):
        logger.info("Detecting exchange for API key")
        for exchange_id in ccxt.exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                })
                await exchange.load_markets()
                self.exchanges[exchange_id] = exchange
                logger.info(f"Detected exchange: {exchange_id}")
                return exchange
            except Exception as e:
                logger.debug(f"Exchange {exchange_id} not matched: {str(e)}")
                continue
        logger.error("No exchange detected for the provided API key")
        return None

    async def close(self):
        """
        Close all exchange connections.
        """
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed exchange connection for {exchange_id}")
            except Exception as e:
                logger.error(f"Failed to close exchange {exchange_id}: {str(e)}")
        self.exchanges.clear()
