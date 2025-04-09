import ccxt.async_support as ccxt
import asyncio
import redis.asyncio as redis
import json
import logging

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

class ExchangeDetector:
    """
    Detect the correct exchange for given API keys with Redis caching.
    """

    def __init__(self):
        self.exchanges = ['mexc', 'binance', 'bybit', 'kucoin']  # Список поддерживаемых бирж
        self.redis_key_prefix = "exchange_detector"

    async def detect_exchange(self, api_key, api_secret):
        """
        Detect the exchange by testing API keys.

        Args:
            api_key (str): API key.
            api_secret (str): API secret.

        Returns:
            tuple: (exchange_name, exchange_instance) if detected, raises ValueError otherwise.
        """
        # Проверяем кэш
        cache_key = f"{self.redis_key_prefix}:{api_key}"
        redis_client = await get_redis_client()
        try:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                exchange_name = cached_result.decode()
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                })
                return exchange_name, exchange
        except Exception as e:
            logger.error(f"Failed to check cache for API key: {type(e).__name__}: {str(e)}")
        finally:
            await redis_client.close()

        # Если в кэше нет, выполняем детекцию
        for exchange_name in self.exchanges:
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            try:
                await exchange.fetch_balance()
                # Сохраняем результат в кэш
                redis_client = await get_redis_client()
                try:
                    await redis_client.set(cache_key, exchange_name, ex=86400)
                except Exception as e:
                    logger.error(f"Failed to cache exchange detection result: {type(e).__name__}: {str(e)}")
                finally:
                    await redis_client.close()
                return exchange_name, exchange
            except Exception:
                await exchange.close()
                continue
        raise ValueError("Could not detect exchange for provided API keys")
