import asyncpg
import logging

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user='trading_user',
            password='password',
            database='trading_bot',
            host='localhost'
        )
        logger.info("Connected to PostgreSQL database")

    async def add_user(self, user_id, api_key, api_secret):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO users (user_id, api_key, api_secret)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET api_key = $2, api_secret = $3
                """,
                user_id, api_key, api_secret
            )
        logger.info(f"Added/Updated user {user_id}")

    async def get_users(self):
        async with self.pool.acquire() as connection:
            rows = await connection.fetch("SELECT user_id, api_key, api_secret FROM users")
        return {row['user_id']: {'api_key': row['api_key'], 'api_secret': row['api_secret']} for row in rows}

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Closed PostgreSQL connection")
