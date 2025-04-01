from logging_setup import logger_main
from symbol_handler import validate_symbol

async def fetch_ticker(exchange, symbol):
    """Fetches ticker data for a symbol from the exchange."""
    try:
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange.id}")
            return None

        bid = ticker.get('bid')
        ask = ticker.get('ask')
        last = ticker.get('last')
        logger_main.info(f"Fetched ticker for {symbol} on {exchange.id}: bid={bid}, ask={ask}, last={last}")
        return ticker
    except Exception as e:
        logger_main.error(f"Error fetching ticker for {symbol} on {exchange.id}: {e}")
        return None

__all__ = ['fetch_ticker']
