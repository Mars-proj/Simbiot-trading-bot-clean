from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def fetch_symbol_data(exchange_id, user_id, symbol, testnet=False):
    """Fetches data for a specific symbol."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return None
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Load markets to get symbol data
        await exchange.load_markets()
        if symbol not in exchange.markets:
            logger_main.error(f"Symbol {symbol} not found on {exchange_id}")
            return None

        market = exchange.markets[symbol]
        symbol_data = {
            'symbol': symbol,
            'precision': market.get('precision', {}),
            'limits': market.get('limits', {}),
            'fees': market.get('fees', {}),
            'active': market.get('active', True)
        }
        logger_main.info(f"Fetched symbol data for {symbol} on {exchange_id}: {symbol_data}")
        return symbol_data
    except Exception as e:
        logger_main.error(f"Error fetching symbol data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_symbol_data']
