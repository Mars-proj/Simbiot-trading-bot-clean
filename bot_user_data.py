from logging_setup import logger_main
from config_keys import API_KEYS

class UserData:
    """Manages user data and status."""
    def __init__(self, users=None):
        self.user_data = users if users is not None else {
            "user1": {"status": "active"},
            "user2": {"status": "active"}
        }
        logger_main.info(f"Initialized UserData with users: {list(self.user_data.keys())}")

    def get_user_status(self, user_id):
        """Gets the status of a user."""
        try:
            if user_id not in self.user_data:
                logger_main.error(f"User {user_id} not found")
                return None
            return self.user_data[user_id]["status"]
        except Exception as e:
            logger_main.error(f"Error getting status for user {user_id}: {e}")
            return None

    def has_api_keys(self, user_id, exchange_id):
        """Checks if the user has API keys for the specified exchange."""
        try:
            if user_id not in API_KEYS:
                logger_main.error(f"User {user_id} not found in API_KEYS")
                return False
            if exchange_id not in API_KEYS[user_id]:
                logger_main.error(f"Exchange {exchange_id} not found for user {user_id}")
                return False
            return True
        except Exception as e:
            logger_main.error(f"Error checking API keys for user {user_id} on {exchange_id}: {e}")
            return False

user_data = UserData()

__all__ = ['user_data']
