# exchange_pool.py
import ccxt.async_support as ccxt
import asyncio
import logging
import redis.asyncio as redis
import json
import time

logger = logging.getLogger("main")

class ExchangePool:
    def __init__(self, api_key, api_secret, user):
        self.api_key = api_key
        self.api_secret = api_secret
        self.user = user
        self.exchange = None
        self.rate_limit_semaphore = asyncio.Semaphore(10)  # Ограничение на 10 одновременных запросов
        self.redis_client = None

    async def get_redis_client(self):
        """Инициализация Redis клиента."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url("redis://localhost:6379/0")
        return self.redis_client

    async def __aenter__(self):
        self.exchange = ccxt.mexc({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'rateLimit': 100,
        })
        logger.debug(f"Created exchange for user {self.user}: {self.exchange}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange is not None:
            await self.exchange.close()
            logger.debug(f"Closed exchange for user {self.user}")
        if self.redis_client is not None:
            await self.redis_client.close()

    def get_markets(self):
        if self.exchange is None:
            logger.error("Exchange not initialized for get_markets")
            return []
        return self.exchange.markets

    async def fetch_ohlcv(self, symbol, timeframe, limit=100):
        """Кэширует и возвращает OHLCV данные."""
        cache_key = f"ohlcv:{symbol}:{timeframe}:{limit}"
        redis_client = await self.get_redis_client()
        try:
            # Проверяем кэш
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached OHLCV for {symbol}")
                return json.loads(cached_data.decode())

            # Ограничиваем частоту запросов
            async with self.rate_limit_semaphore:
                data = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                # Сохраняем в кэш на 5 минут
                await redis_client.set(cache_key, json.dumps(data), ex=300)
                return data
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {type(e).__name__}: {str(e)}")
            return None
        finally:
            if redis_client is not None:
                await redis_client.close()

    async def fetch_ticker(self, symbol):
        """Кэширует и возвращает данные тикера."""
        cache_key = f"ticker:{symbol}"
        redis_client = await self.get_redis_client()
        try:
            # Проверяем кэш
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached ticker for {symbol}")
                return json.loads(cached_data.decode())

            # Ограничиваем частоту запросов
            async with self.rate_limit_semaphore:
                data = await self.exchange.fetch_ticker(symbol)
                # Сохраняем в кэш на 1 минуту
                await redis_client.set(cache_key, json.dumps(data), ex=60)
                return data
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {type(e).__name__}: {str(e)}")
            return None
        finally:
            if redis_client is not None:
                await redis_client.close()
