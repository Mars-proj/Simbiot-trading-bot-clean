import ccxt.async_support as ccxt
from logging_setup import logger_main

def normalize_symbol(symbol):
    """Normalizes the symbol format (e.g., converts to uppercase, removes invalid characters)."""
    try:
        if not isinstance(symbol, str):
            raise ValueError("Symbol must be a string")
        normalized = symbol.upper().replace(" ", "")
        logger_main.info(f"Normalized symbol: {symbol} -> {normalized}")
        return normalized
    except Exception as e:
        logger_main.error(f"Error normalizing symbol {symbol}: {e}")
        return None

def validate_symbol(symbol):
    """Validates the symbol format."""
    try:
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("Symbol must be a non-empty string")
        if '/' not in symbol:
            raise ValueError("Symbol must contain '/' (e.g., BTC/USDT)")
        logger_main.info(f"Validated symbol: {symbol}")
        return True
    except Exception as e:
        logger_main.error(f"Error validating symbol {symbol}: {e}")
        return False

async def validate_symbol_with_markets(exchange, symbol):
    """Validates the symbol using exchange.load_markets()."""
    try:
        if not isinstance(exchange, ccxt.async_support.BaseExchange):
            raise ValueError("Exchange must be a ccxt.async_support.BaseExchange instance")
        if not validate_symbol(symbol):
            return False
        markets = await exchange.load_markets()
        if symbol not in markets:
            logger_main.error(f"Symbol {symbol} not supported on exchange {exchange.id}")
            return False
        logger_main.info(f"Symbol {symbol} validated successfully on exchange {exchange.id}")
        return True
    except Exception as e:
        logger_main.error(f"Error validating symbol {symbol} on exchange {exchange.id}: {e}")
        return False

__all__ = ['normalize_symbol', 'validate_symbol', 'validate_symbol_with_markets']
