from logging_setup import logger_main
from config_keys import API_KEYS

class BotUserData:
    """Manages user data for the trading bot."""
    def __init__(self, user_id, testnet=False):
        self.user_id = user_id
        self.testnet = testnet
        self.api_keys = API_KEYS.get(user_id, {})
        logger_main.info(f"Initialized BotUserData for user {user_id}, testnet={testnet}")

    def get_api_keys(self, exchange_id):
        """Returns API keys for the specified exchange."""
        keys = self.api_keys.get(exchange_id, {})
        if not keys:
            logger_main.error(f"No API keys found for user {self.user_id} on {exchange_id}")
            return None
        return keys
