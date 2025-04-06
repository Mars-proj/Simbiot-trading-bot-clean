import asyncio
import ccxt.async_support as ccxt
from logging_setup import logger_main
from bot_user_data import BotUserData

class ExchangePool:
    """Manages a pool of exchange instances for multiple users."""
    def __init__(self):
        self.exchanges = {}

    async def get_exchange(self, exchange_id, user_id, testnet=False):
        """Gets or creates an exchange instance for the user."""
        key = f"{exchange_id}:{user_id}"
        if key in self.exchanges:
            logger_main.debug(f"Returning existing exchange instance for {key}")
            return self.exchanges[key]

        try:
            user_data = BotUserData(user_id, testnet)
            api_keys = user_data.get_api_keys(exchange_id)
            if not api_keys:
                logger_main.error(f"No API keys for {exchange_id}:{user_id}")
                return None

            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'apiKey': api_keys['api_key'],
                'secret': api_keys['api_secret'],
                'enableRateLimit': True,
            })
            if testnet:
                exchange.set_sandbox_mode(True)

            self.exchanges[key] = exchange
            logger_main.info(f"Created new exchange instance for {key}")
            return exchange

        except Exception as e:
            logger_main.error(f"Error creating exchange instance for {key}: {e}")
            return None

    async def close_exchange(self, exchange_id, user_id):
        """Closes an exchange instance."""
        key = f"{exchange_id}:{user_id}"
        if key in self.exchanges:
            try:
                await self.exchanges[key].close()
                logger_main.info(f"Closed exchange instance for {key}")
            except Exception as e:
                logger_main.error(f"Error closing exchange instance for {key}: {e}")
            finally:
                del self.exchanges[key]

    async def close_all(self):
        """Closes all exchange instances."""
        tasks = []
        for key in list(self.exchanges.keys()):
            tasks.append(self.close_exchange(*key.split(':')))
        await asyncio.gather(*tasks)
