from logging_setup import logger_main
from redis_client import RedisClient
import json

class BotUserData:
    def __init__(self):
        self.redis = RedisClient()
        self.users_key = "bot_users"

    async def _load_users(self):
        """Loads users from Redis."""
        try:
            users_data = await self.redis.get(self.users_key)
            if users_data:
                return json.loads(users_data)
            return {}
        except Exception as e:
            logger_main.error(f"Error loading users from Redis: {e}")
            return {}

    async def _save_users(self, users):
        """Saves users to Redis."""
        try:
            await self.redis.set(self.users_key, json.dumps(users))
        except Exception as e:
            logger_main.error(f"Error saving users to Redis: {e}")

    async def add_user(self, user_id, api_keys=None, status=True):
        """Adds a new user with API keys and status."""
        try:
            users = await self._load_users()
            if user_id in users:
                logger_main.warning(f"User {user_id} already exists")
                return False

            users[user_id] = {
                'api_keys': api_keys or {},
                'status': status
            }
            await self._save_users(users)
            logger_main.info(f"Added user {user_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error adding user {user_id}: {e}")
            return False

    async def get_user_status(self, user_id):
        """Gets the status of a user."""
        try:
            users = await self._load_users()
            user = users.get(user_id)
            if user is None:
                return False
            return user.get('status', False)
        except Exception as e:
            logger_main.error(f"Error getting status for user {user_id}: {e}")
            return False

    async def has_api_keys(self, user_id, exchange_id):
        """Checks if the user has API keys for the specified exchange."""
        try:
            users = await self._load_users()
            user = users.get(user_id)
            if user is None:
                return False
            api_keys = user.get('api_keys', {})
            return exchange_id in api_keys and 'api_key' in api_keys[exchange_id] and 'api_secret' in api_keys[exchange_id]
        except Exception as e:
            logger_main.error(f"Error checking API keys for user {user_id} on {exchange_id}: {e}")
            return False

    async def get_api_keys(self, user_id, exchange_id):
        """Gets the API keys for a user and exchange."""
        try:
            users = await self._load_users()
            user = users.get(user_id)
            if user is None:
                return None
            api_keys = user.get('api_keys', {})
            return api_keys.get(exchange_id)
        except Exception as e:
            logger_main.error(f"Error getting API keys for user {user_id} on {exchange_id}: {e}")
            return None

user_data = BotUserData()

__all__ = ['user_data']
