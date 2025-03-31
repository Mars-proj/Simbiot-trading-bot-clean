from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS
from exchange_utils import fetch_ticker

async def filter_symbols(exchange, symbols, min_volume=100000, min_liquidity=0.1):
    """Filters symbols based on criteria like minimum volume and liquidity."""
    try:
        filtered_symbols = []
        for symbol in symbols:
            ticker = await fetch_ticker(exchange, symbol)
            if not ticker:
                logger_main.info(f"Symbol {symbol} filtered out: failed to fetch ticker")
                continue

            volume = ticker.get('baseVolume', 0)
            bid_ask_spread = (ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('ask', 1) if ticker.get('ask', 0) > 0 else float('inf')
            liquidity = 1 / bid_ask_spread if bid_ask_spread > 0 else 0

            if volume >= min_volume and liquidity >= min_liquidity:
                filtered_symbols.append(symbol)
            else:
                logger_main.info(f"Symbol {symbol} filtered out: volume={volume}, liquidity={liquidity}")

        # Additional filtering based on supported symbols
        filtered_symbols = [symbol for symbol in filtered_symbols if symbol in SUPPORTED_SYMBOLS]
        logger_main.info(f"Filtered {len(filtered_symbols)} symbols: {filtered_symbols}")
        return filtered_symbols
    except Exception as e:
        logger_main.error(f"Error filtering symbols: {e}")
        return []

__all__ = ['filter_symbols']
