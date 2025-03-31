from logging_setup import logger_main
from exchange_factory import create_exchange
from config_keys import SUPPORTED_EXCHANGES

async def validate_symbol(exchange_id, user_id, symbol, testnet=False):
    """Validates a symbol by checking if it exists on the specified exchange."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return False
        if not isinstance(symbol, str):
            logger_main.error(f"Symbol must be a string, got {type(symbol)}")
            return False

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Load markets and check if symbol exists
        await exchange.load_markets()
        if symbol not in exchange.markets:
            logger_main.error(f"Symbol {symbol} not found on {exchange_id}")
            return False

        # Check if symbol is active
        market = exchange.markets[symbol]
        if not market.get('active', True):
            logger_main.error(f"Symbol {symbol} is not active on {exchange_id}")
            return False

        logger_main.info(f"Symbol {symbol} validated successfully on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error validating symbol {symbol} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['validate_symbol']
