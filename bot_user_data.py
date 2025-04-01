from logging_setup import logger_main
from cache_utils import CacheUtils

class BotUserData:
    def __init__(self):
        self.cache = CacheUtils()

    async def get_user_status(self, user_id):
        """Checks if the user is active."""
        try:
            key = f"user_status:{user_id}"
            status = await self.cache.get(key)
            return status if status is not None else True  # Default to active
        except Exception as e:
            logger_main.error(f"Error getting user status for {user_id}: {e}")
            return False

    async def has_api_keys(self, exchange_id, user_id):
        """Checks if the user has API keys for the exchange."""
        try:
            from config_keys import API_KEYS
            return user_id in API_KEYS and exchange_id in API_KEYS[user_id]
        except Exception as e:
            logger_main.error(f"Error checking API keys for {user_id} on {exchange_id}: {e}")
            return False

    async def save_user_trade(self, user_id, trade_data):
        """Saves a trade to the user's cache."""
        try:
            key = f"user_trades:{user_id}"
            await self.cache.append_to_list(key, trade_data)
            logger_main.debug(f"Saved trade for user {user_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error saving trade for user {user_id}: {e}")
            return False

    async def get_user_trades(self, user_id):
        """Retrieves all trades for the user."""
        try:
            key = f"user_trades:{user_id}"
            trades = await self.cache.get_list(key)
            return trades
        except Exception as e:
            logger_main.error(f"Error retrieving trades for user {user_id}: {e}")
            return []

    async def save_user_preferences(self, user_id, preferences):
        """Saves user preferences to cache."""
        try:
            key = f"user_preferences:{user_id}"
            await self.cache.setex(key, 86400, preferences)
            logger_main.debug(f"Saved preferences for user {user_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error saving preferences for user {user_id}: {e}")
            return False

    async def get_user_preferences(self, user_id):
        """Retrieves user preferences from cache."""
        try:
            key = f"user_preferences:{user_id}"
            preferences = await self.cache.get(key)
            return preferences
        except Exception as e:
            logger_main.error(f"Error retrieving preferences for user {user_id}: {e}")
            return None

__all__ = ['BotUserData']
