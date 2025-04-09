import asyncpg
import logging
import json
import ccxt.async_support as ccxt

logger = logging.getLogger("main")

class UserManager:
    """
    Manage user data stored in PostgreSQL.
    """

    def __init__(self, dsn="postgresql://user:password@localhost:5432/trading_bot"):
        """
        Initialize UserManager with a PostgreSQL connection.

        Args:
            dsn (str): PostgreSQL connection string.
        """
        self.dsn = dsn
        self.pool = None

    async def __aenter__(self):
        """Enter the async context, initialize PostgreSQL connection pool."""
        self.pool = await asyncpg.create_pool(self.dsn)
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                api_key TEXT NOT NULL,
                api_secret TEXT NOT NULL
            )
        """)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the async context, close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()

    async def add_user(self, user_id, api_key, api_secret):
        """
        Add a new user to the database with API key validation.

        Args:
            user_id (str): User identifier.
            api_key (str): API key.
            api_secret (str): API secret.

        Raises:
            ValueError: If API keys are invalid.
        """
        # Валидация API-ключей
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        try:
            await exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Invalid API keys for user {user_id}: {type(e).__name__}: {str(e)}")
            raise ValueError("Invalid API keys")
        finally:
            await exchange.close()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO users (user_id, api_key, api_secret) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO UPDATE SET api_key = $2, api_secret = $3",
                    user_id, api_key, api_secret
                )
            logger.info(f"Added/updated user {user_id}")
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {type(e).__name__}: {str(e)}")
            raise

    async def remove_user(self, user_id):
        """
        Remove a user from the database.

        Args:
            user_id (str): User identifier.
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
            logger.info(f"Removed user {user_id}")
        except Exception as e:
            logger.error(f"Failed to remove user {user_id}: {type(e).__name__}: {str(e)}")
            raise

    async def get_users(self):
        """
        Retrieve all users from the database.

        Returns:
            dict: Dictionary of user IDs and their credentials.
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM users")
            users = {row['user_id']: {"api_key": row['api_key'], "api_secret": row['api_secret']} for row in rows}
            return users
        except Exception as e:
            logger.error(f"Failed to load users from PostgreSQL: {type(e).__name__}: {str(e)}")
            return {}
