import ccxt.async_support as ccxt
import asyncio

class ExchangeDetector:
    """
    Detect the correct exchange for given API keys.
    """

    def __init__(self):
        self.exchanges = ['mexc', 'binance', 'bybit', 'kucoin']  # Список поддерживаемых бирж

    async def detect_exchange(self, api_key, api_secret):
        """
        Detect the exchange by testing API keys.

        Args:
            api_key (str): API key.
            api_secret (str): API secret.

        Returns:
            tuple: (exchange_name, exchange_instance) if detected, raises ValueError otherwise.
        """
        for exchange_name in self.exchanges:
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            try:
                await exchange.fetch_balance()
                return exchange_name, exchange
            except Exception:
                await exchange.close()
                continue
        raise ValueError("Could not detect exchange for provided API keys")
