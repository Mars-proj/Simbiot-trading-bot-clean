from exchange_factory import ExchangeFactory

class ExchangePool:
    """
    Pool of exchange instances for multiple exchanges.
    """

    def __init__(self):
        self.exchanges = {}

    def get_exchange(self, exchange_name, credentials):
        """
        Get or create an exchange instance.

        Args:
            exchange_name (str): Name of the exchange.
            credentials (dict): API credentials with 'api_key' and 'api_secret'.

        Returns:
            Exchange instance.
        """
        key = f"{exchange_name}:{credentials['api_key']}"
        if key not in self.exchanges:
            self.exchanges[key] = ExchangeFactory.create_exchange(exchange_name, credentials)
        return self.exchanges[key]

    async def close_all(self):
        """
        Close all exchange connections.
        """
        for exchange in self.exchanges.values():
            await exchange.close()
