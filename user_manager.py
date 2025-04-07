# user_manager.py
import redis.asyncio as redis
import logging
from config_keys import USER_API_KEYS

logger = logging.getLogger("main")

class UserManager:
    def __init__(self):
        self.redis_client = None

    async def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = await redis.from_url("redis://localhost:6379/0")
        return self.redis_client

    async def get_users(self):
        redis_client = await self.get_redis_client()
        try:
            # Проверяем, есть ли пользователи в Redis
            users_data = await redis_client.hgetall("users")
            if users_data:
                users = {user.decode(): eval(cred.decode()) for user, cred in users_data.items()}
                logger.info(f"Loaded {len(users)} users from Redis")
                return users
            else:
                # Если Redis пуст, используем тестовых пользователей из config_keys.py
                logger.warning("No users found in Redis, using test users from config_keys.py")
                users = USER_API_KEYS
                # Сохраняем тестовых пользователей в Redis
                for user, creds in users.items():
                    await redis_client.hset("users", user, str(creds))
                logger.info(f"Saved {len(users)} test users to Redis")
                return users
        except Exception as e:
            logger.error(f"Failed to load users from Redis: {type(e).__name__}: {str(e)}")
            # В случае ошибки возвращаем тестовых пользователей
            return USER_API_KEYS

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
