from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
import os

async def get_test_symbols(exchange_id, user_id, testnet=False):
    """Fetches test symbols dynamically from the exchange with volume filtering."""
    try:
        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return []

        # Load markets
        markets = await exchange.load_markets()
        symbols = list(markets.keys())

        # Validate symbols and filter by volume
        min_volume_threshold = float(os.getenv("MIN_VOLUME_THRESHOLD", 1000))
        valid_symbols = []
        for symbol in symbols:
            if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
                continue

            ticker = await exchange.fetch_ticker(symbol)
            if not ticker:
                continue

            volume = ticker.get('baseVolume', 0)
            if volume < min_volume_threshold:
                logger_main.debug(f"Symbol {symbol} volume {volume} below threshold {min_volume_threshold}, skipping")
                continue

            valid_symbols.append(symbol)

        logger_main.info(f"Fetched {len(valid_symbols)} test symbols for {exchange_id}")
        return valid_symbols
    except Exception as e:
        logger_main.error(f"Error fetching test symbols for {exchange_id}: {e}")
        return []
    finally:
        await exchange.close()

__all__ = ['get_test_symbols']
