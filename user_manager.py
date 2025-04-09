# user_manager.py
import logging
import json
import redis.asyncio as redis

logger = logging.getLogger("main")

class UserManager:
    def __init__(self):
        self.redis_client = None

    async def __aenter__(self):
        self.redis_client = await redis.from_url("redis://localhost:6379/0")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Закрывает соединение с Redis."""
        if self.redis_client:
            logger.debug("Closing Redis connection in UserManager")
            await self.redis_client.close()
            self.redis_client = None

    async def get_users(self):
        """Загружает пользователей из Redis."""
        try:
            users_data = await self.redis_client.get("users")
            if users_data:
                return json.loads(users_data.decode())
            else:
                logger.warning("No users found in Redis, returning empty dict")
                return {}
        except redis.RedisError as e:
            logger.error(f"Failed to load users from Redis: {type(e).__name__}: {str(e)}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode users JSON: {type(e).__name__}: {str(e)}")
            return {}
