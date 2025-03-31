import aioredis
from logging_setup import logger_main
import os

class RedisClient:
    """Manages Redis client operations."""
    def __init__(self, redis_url=None):
        self.redis_url = redis_url if redis_url else os.getenv("REDIS_URL", "redis://localhost")
        self.redis_client = None
        self.initialized = False

    async def init_redis(self):
        """Initializes the Redis client if not already initialized."""
        if self.initialized:
            return
        try:
            self.redis_client = await aioredis.create_redis_pool(self.redis_url)
            logger_main.info(f"Redis client initialized successfully at {self.redis_url}")
            self.initialized = True
        except Exception as e:
            logger_main.error(f"Error initializing Redis client: {e}")
            self.redis_client = None
            self.initialized = False

    async def get(self, key):
        """Gets a value from Redis by key."""
        try:
            await self.init_redis()
            if self.redis_client is None:
                raise ValueError("Redis client not initialized")
            return await self.redis_client.get(key, encoding='utf-8')
        except Exception as e:
            logger_main.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def set(self, key, value, ex=None):
        """Sets a value in Redis with an optional expiration time."""
        try:
            await self.init_redis()
            if self.redis_client is None:
                raise ValueError("Redis client not initialized")
            await self.redis_client.set(key, value, expire=ex)
            logger_main.info(f"Set key {key} in Redis")
        except Exception as e:
            logger_main.error(f"Error setting key {key} in Redis: {e}")

redis_client = RedisClient()

__all__ = ['redis_client']
