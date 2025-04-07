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
        retry_count = 3
        for attempt in range(retry_count):
            try:
                self.exchange = ccxt.mexc({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'rateLimit': 1000,
                })
                logger.info(f"Attempting to load markets for user {self.user} (attempt {attempt + 1}/{retry_count})")
                await self.exchange.load_markets()
                logger.info(f"Successfully loaded markets for user {self.user}")
                return self.exchange
            except Exception as e:
                logger.error(f"Failed to initialize exchange for user {self.user} on attempt {attempt + 1}: {e}")
                if attempt < retry_count - 1:
                    logger.info(f"Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    raise Exception(f"Failed to initialize exchange for user {self.user} after {retry_count} attempts: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            try:
                await self.exchange.close()
                logger.info(f"Closed exchange instance for mexc:user {self.user}")
            except Exception as e:
                logger.error(f"Failed to close exchange for user {self.user}: {e}")
