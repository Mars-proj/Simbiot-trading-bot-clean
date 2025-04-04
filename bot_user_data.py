# bot_user_data.py
from cache_utils import RedisClient

class BotUserData:
    def __init__(self, user_id, exchange_id, testnet):
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.testnet = testnet
        self.cache = RedisClient(f"redis://localhost:6379")
