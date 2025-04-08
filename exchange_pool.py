# exchange_pool.py
import ccxt.async_support as ccxt
import logging

logger = logging.getLogger("main")

class ExchangePool:
    def __init__(self, api_key, api_secret, user):
        self.api_key = api_key
        self.api_secret = api_secret
        self.user = user
        self.exchange = None

    async def __aenter__(self):
        logger.debug(f"Initializing MEXC exchange for user {self.user}")
        self.exchange = ccxt.mexc({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        try:
            # Загружаем рынки при инициализации
            await self.exchange.load_markets()
            logger.debug(f"Markets loaded for user {self.user}: {len(self.exchange.markets)} markets available")
        except Exception as e:
            logger.error(f"Failed to load markets for user {self.user}: {type(e).__name__}: {str(e)}")
            raise
        return self.exchange

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            logger.debug(f"Closing exchange for user {self.user}")
            await self.exchange.close()

    def get_markets(self):
        if not self.exchange:
            logger.error(f"Exchange not initialized for user {self.user}")
            return {}
        return self.exchange.markets

    async def fetch_ohlcv(self, symbol, timeframe, limit):
        if not self.exchange:
            logger.error(f"Exchange not initialized for user {self.user}")
            return []
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {type(e).__name__}: {str(e)}")
            return []
