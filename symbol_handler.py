from logging_setup import logger_main
from exchange_factory import create_exchange
import os

async def validate_symbol(exchange_id, user_id, symbol, testnet=False):
    """Validates a symbol dynamically using the exchange API."""
    try:
        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False

        # Load markets
        markets = await exchange.load_markets()
        if symbol not in markets:
            logger_main.error(f"Symbol {symbol} not found on {exchange_id}")
            return False

        # Check if symbol is active
        market = markets[symbol]
        if not market.get('active', True):
            logger_main.error(f"Symbol {symbol} is not active on {exchange_id}")
            return False

        # Check minimum trading volume (example threshold, can be made configurable)
        min_volume_threshold = float(os.getenv("MIN_VOLUME_THRESHOLD", 1000))
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return False

        volume = ticker.get('baseVolume', 0)
        if volume < min_volume_threshold:
            logger_main.error(f"Symbol {symbol} volume {volume} is below threshold {min_volume_threshold} on {exchange_id}")
            return False

        logger_main.info(f"Symbol {symbol} validated successfully on {exchange_id}")
        return True
    except Exception as e:
        logger_main.error(f"Error validating symbol {symbol} on {exchange_id}: {e}")
        return False
    finally:
        await exchange.close()

__all__ = ['validate_symbol']
