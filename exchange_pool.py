# exchange_pool.py
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
        # Проверяем, есть ли API-ключ и секрет
        if self.api_key and self.api_secret:
            self.exchange = ccxt.mexc({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'timeout': 30000,
                'rateLimit': 1000,
            })
            # Указываем defaultType через атрибут
            self.exchange.options['defaultType'] = 'spot'
            logger.info(f"Exchange initialized for user {self.user} with API key, defaultType=spot")
            # Проверяем доступность API-ключа
            try:
                balance = await self.exchange.fetch_balance()
                logger.info(f"API key is valid for user {self.user}, fetched balance: {balance.get('total', {})}")
            except Exception as e:
                logger.error(f"API key validation failed for user {self.user}: {type(e).__name__}: {str(e)}")
                # Переключаемся на публичный доступ
                self.exchange = ccxt.mexc({
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'rateLimit': 1000,
                })
                self.exchange.options['defaultType'] = 'spot'
                logger.info(f"Fallback to public access for user {self.user}, defaultType=spot")
        else:
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'timeout': 30000,
                'rateLimit': 1000,
            })
            self.exchange.options['defaultType'] = 'spot'
            logger.info(f"Exchange initialized for user {self.user} without API key (public access), defaultType=spot")

        # Проверим доступные рынки
        try:
            # Явно указываем params с defaultType
            markets = await self.exchange.fetch_markets(params={'type': 'spot'})
            logger.info(f"Loaded {len(markets)} markets for user {self.user}")
            logger.info(f"First 5 market symbols for user {self.user}: {list(market['symbol'] for market in markets)[:5]}")
            # Дополнительное логирование типов рынков
            market_types = set(market['type'] for market in markets)
            logger.info(f"Market types for user {self.user}: {list(market_types)}")
        except Exception as e:
            logger.error(f"Failed to load markets for user {self.user}: {type(e).__name__}: {str(e)}")

        return self.exchange

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            try:
                await self.exchange.close()
                logger.info(f"Closed exchange instance for mexc:user {self.user}")
            except Exception as e:
                logger.error(f"Failed to close exchange for user {self.user}: {type(e).__name__}: {str(e)}")
