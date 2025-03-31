from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS

class BalanceManager:
    """Manages user balances."""
    def __init__(self, user_id):
        self.user_id = user_id

    async def get_balance(self, exchange):
        """Fetches the user's balance from the exchange."""
        try:
            balance = await exchange.fetch_balance()
            logger_main.info(f"Fetched balance for user {self.user_id} on {exchange.id}: {balance}")
            return balance
        except Exception as e:
            logger_main.error(f"Error fetching balance for user {self.user_id} on {exchange.id}: {e}")
            return None

    async def get_holdings(self, exchange):
        """Fetches the user's current holdings."""
        try:
            balance = await self.get_balance(exchange)
            if not balance:
                return None
            holdings = {asset: details for asset, details in balance.items() if details['total'] > 0}
            logger_main.info(f"Fetched holdings for user {self.user_id} on {exchange.id}: {holdings}")
            return holdings
        except Exception as e:
            logger_main.error(f"Error fetching holdings for user {self.user_id} on {exchange.id}: {e}")
            return None

__all__ = ['BalanceManager']
