import ccxt.async_support as ccxt

class ExchangeFactory:
    """
    Factory for creating exchange instances.
    """

    SUPPORTED_EXCHANGES = ['mexc', 'binance', 'bybit', 'kucoin']  # Список поддерживаемых бирж

    @staticmethod
    def create_exchange(exchange_name, credentials):
        """
        Create an exchange instance.

        Args:
            exchange_name (str): Name of the exchange (e.g., 'mexc').
            credentials (dict): API credentials with 'api_key' and 'api_secret'.

        Returns:
            Exchange instance.

        Raises:
            ValueError: If the exchange is not supported.
        """
        if exchange_name not in ExchangeFactory.SUPPORTED_EXCHANGES:
            raise ValueError(f"Exchange {exchange_name} is not supported. Supported exchanges: {ExchangeFactory.SUPPORTED_EXCHANGES}")
        
        exchange_class = getattr(ccxt, exchange_name)
        return exchange_class({
            'apiKey': credentials['api_key'],
            'secret': credentials['api_secret'],
            'enableRateLimit': True,
        })

    @staticmethod
    async def validate_exchange(exchange):
        """
        Validate an exchange instance by checking API key validity.

        Args:
            exchange: Exchange instance.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            await exchange.fetch_balance()
            return True
        except Exception:
            return False
