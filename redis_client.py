import os
import redis.asyncio as redis
from logging_setup import logger_main

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None
        self._initialize()

    def _initialize(self):
        try:
            self.client = redis.from_url(self.redis_url)
            logger_main.info(f"Initialized Redis client with URL: {self.redis_url}")
        except Exception as e:
            logger_main.error(f"Error initializing Redis client: {e}")
            raise

    async def set(self, key, value):
        try:
            await self.client.set(key, value)
            return True
        except Exception as e:
            logger_main.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def get(self, key):
        try:
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger_main.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def setex(self, key, ttl, value):
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger_main.error(f"Error setting key {key} with TTL in Redis: {e}")
            return False

    async def delete(self, key):
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger_main.error(f"Error deleting key {key} from Redis: {e}")
            return False

    async def keys(self, pattern):
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger_main.error(f"Error fetching keys with pattern {pattern} from Redis: {e}")
            return []

    async def ttl(self, key):
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger_main.error(f"Error getting TTL for key {key} from Redis: {e}")
            return -1

__all__ = ['RedisClient']
