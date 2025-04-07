import redis.asyncio as redis
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("main")

class UserManager:
    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis = None

    async def connect(self):
        if self.redis is None:
            self.redis = await redis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
            logger.info("Connected to Redis")

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection")

    async def get_users(self):
        await self.connect()
        users = {}
        user_keys = await self.redis.keys('user:*')
        for key in user_keys:
            user_id = key.decode().split(':')[1]
            user_data = await self.redis.hgetall(key)
            users[user_id] = {
                'api_key': user_data[b'api_key'].decode(),
                'api_secret': user_data[b'api_secret'].decode()
            }
        return users

    async def add_user(self, user_id, api_key, api_secret):
        await self.connect()
        await self.redis.hset(f'user:{user_id}', mapping={
            'api_key': api_key,
            'api_secret': api_secret
        })
        logger.info(f"Added user {user_id} to Redis")
