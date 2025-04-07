import ccxt.async_support as ccxt
import logging
import asyncio

logger = logging.getLogger("main")

class ExchangePool:
    def __init__(self, api_key, api_secret, user):
        self.api_key = api_key
        self.api_secret = api_secret
        self.user = user
        self.exchange = None

    async def __aenter__(self):
        logger.debug(f"Initializing exchange for user {self.user}")
        self.exchange = ccxt.mexc({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'timeout': 30000,
            'rateLimit': 1000,
            'options': {
                'defaultType': 'spot',  # Указываем, что нам нужен спотовый рынок
            }
        })
        logger.info(f"Exchange initialized for user {self.user} with defaultType=spot")
        return self.exchange

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            try:
                await self.exchange.close()
                logger.info(f"Closed exchange instance for mexc:user {self.user}")
            except Exception as e:
                logger.error(f"Failed to close exchange for user {self.user}: {e}")
