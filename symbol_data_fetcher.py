from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from cache_utils import CacheUtils

async def fetch_symbol_data(exchange_id, user_id, symbol, testnet=False):
    """Fetches symbol data dynamically from the exchange with caching."""
    try:
        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Validate symbol
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Check cache
        cache = CacheUtils()
        cached_data = await cache.get_symbol_data(symbol)
        if cached_data:
            logger_main.info(f"Retrieved symbol data for {symbol} from cache")
            return cached_data

        # Fetch markets
        await exchange.load_markets()
        if symbol not in exchange.markets:
            logger_main.error(f"Symbol {symbol} not found in markets on {exchange_id}")
            return None

        # Fetch ticker
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
            return None

        # Fetch additional data (e.g., volume, price precision)
        market = exchange.markets[symbol]
        symbol_data = {
            'symbol': symbol,
            'price_precision': market.get('precision', {}).get('price', 8),
            'amount_precision': market.get('precision', {}).get('amount', 8),
            'volume': ticker.get('baseVolume', 0),
            'last_price': ticker.get('last', 0),
            'bid': ticker.get('bid', 0),
            'ask': ticker.get('ask', 0)
        }

        # Cache the data
        await cache.cache_symbol_data(symbol, symbol_data)
        logger_main.info(f"Fetched and cached symbol data for {symbol} on {exchange_id}")
        return symbol_data
    except Exception as e:
        logger_main.error(f"Error fetching symbol data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_symbol_data']
