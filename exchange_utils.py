import ccxt.async_support as ccxt
from logging_setup import logger_main
from symbol_handler import validate_symbol

async def fetch_ticker(exchange, symbol, exchange_id, user_id, testnet=False):
    """Fetches ticker data for a symbol."""
    try:
        if not isinstance(exchange, ccxt.async_support.Exchange):
            logger_main.error(f"Exchange must be a ccxt.async_support.Exchange object, got {type(exchange)}")
            return None
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None
        ticker = await exchange.fetch_ticker(symbol)
        logger_main.info(f"Fetched ticker for {symbol}: bid={ticker.get('bid', 'N/A')}, ask={ticker.get('ask', 'N/A')}")
        return ticker
    except ccxt.NetworkError as e:
        logger_main.error(f"Network error while fetching ticker for {symbol}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger_main.error(f"Exchange error while fetching ticker for {symbol}: {e}")
        return None
    except Exception as e:
        logger_main.error(f"Error fetching ticker for {symbol}: {e}")
        return None

__all__ = ['fetch_ticker']
