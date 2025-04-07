import asyncio
from user_manager import UserManager
from config_keys import API_KEYS

async def main():
    user_manager = UserManager()
    for user_id, exchanges in API_KEYS.items():
        for exchange_id, keys in exchanges.items():
            if exchange_id == 'mexc':  # Мы используем только MEXC
                api_key = keys['api_key']
                api_secret = keys['api_secret']
                await user_manager.add_user(user_id, api_key, api_secret)
    await user_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
