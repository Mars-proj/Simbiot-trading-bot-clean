import ccxt.async_support as ccxt
import logging

logger = logging.getLogger("main")

class ExchangePool:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None

    async def __aenter__(self):
        self.exchange = ccxt.mexc({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        await self.exchange.load_markets()
        return self.exchange

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            await self.exchange.close()
            logger.info(f"Closed exchange instance for mexc:user")
