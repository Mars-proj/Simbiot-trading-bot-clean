from logging_setup import logger_main
from redis_client import RedisClient
from config_keys import validate_api_keys

class BotUserData:
    def __init__(self):
        self.redis = RedisClient()
        self.users = {}

    async def add_user(self, user_id, api_keys=None, active=True):
        """Adds a new user with API keys and status."""
        try:
            if not user_id or not isinstance(user_id, str):
                logger_main.error(f"Invalid user_id: {user_id}")
                return False

            user_data = {
                "api_keys": api_keys or {},
                "active": active
            }
            await self.redis.set(f"user:{user_id}", str(user_data))
            self.users[user_id] = user_data
            logger_main.info(f"Added user {user_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error adding user {user_id}: {e}")
            return False

    async def get_user_status(self, user_id):
        """Gets the status of a user."""
        try:
            user_data = await self.redis.get(f"user:{user_id}")
            if user_data:
                user_data = eval(user_data)  # Safely evaluate the stringified dict
                return user_data.get("active", False)
            return False
        except Exception as e:
            logger_main.error(f"Error getting user status for {user_id}: {e}")
            return False

    async def has_api_keys(self, user_id, exchange_id):
        """Checks if the user has API keys for the specified exchange."""
        try:
            user_data = await self.redis.get(f"user:{user_id}")
            if not user_data:
                return False
            user_data = eval(user_data)
            api_keys = user_data.get("api_keys", {}).get(exchange_id, {})
            if not api_keys:
                return False
            api_key = api_keys.get("api_key")
            api_secret = api_keys.get("api_secret")
            return validate_api_keys(api_key, api_secret)
        except Exception as e:
            logger_main.error(f"Error checking API keys for user {user_id} on {exchange_id}: {e}")
            return False

user_data = BotUserData()

__all__ = ['user_data']
