from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def get_test_symbols(exchange_id, user_id, testnet=False, limit=3):
    """Fetches a list of test symbols from the exchange."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return []
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return []

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return []

        # Load markets
        await exchange.load_markets()
        symbols = list(exchange.markets.keys())

        # Validate and filter symbols
        test_symbols = []
        for symbol in symbols[:limit]:
            if await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
                test_symbols.append(symbol)

        logger_main.info(f"Fetched {len(test_symbols)} test symbols for {exchange_id}: {test_symbols}")
        return test_symbols
    except Exception as e:
        logger_main.error(f"Error fetching test symbols for {exchange_id}: {e}")
        return []
    finally:
        await exchange.close()

__all__ = ['get_test_symbols']
