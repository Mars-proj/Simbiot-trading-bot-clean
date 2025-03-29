import asyncio
import ccxt.async_support as ccxt
from utils import logger_main, log_exception
from exchange_utils import unavailable_symbols, filtered_symbols_cache, symbol_check_cache
from async_exchange_fetcher import async_exchange_fetcher
from redis_client import redis_client
from exchange_factory import create_exchange

async def filter_symbols_for_exchange(preferred_exchange, exchange_data, loop=None):
    """Filters symbols for a given exchange using a single user's API key"""
    logger_main.debug(f"Filtering symbols for {preferred_exchange}")
    cache_key = f"filtered_symbols:{preferred_exchange}"
    cached_symbols = await redis_client.get_json(cache_key)
    if cached_symbols is not None:
        filtered_symbols_cache[preferred_exchange] = cached_symbols
        logger_main.debug(f"Loaded {len(cached_symbols)} cached symbols for {preferred_exchange} from Redis")
        return cached_symbols
    exchange = await create_exchange(preferred_exchange, exchange_data, loop)
    if exchange is None:
        logger_main.error(f"Failed to create exchange for symbol filtering for {preferred_exchange}")
        return []
    logger_main.debug(f"Synchronizing time with {preferred_exchange} server for symbol filtering")
    try:
        await asyncio.wait_for(async_exchange_fetcher.fetch_time(exchange), timeout=10)
        logger_main.debug(f"Time successfully synchronized with {preferred_exchange} server")
    except asyncio.TimeoutError as e:
        logger_main.error(f"Timeout synchronizing time with {preferred_exchange} server: {str(e)}")
        log_exception(f"Timeout synchronizing time: {str(e)}", e)
        await async_exchange_fetcher.close(exchange)
        return []
    except Exception as e:
        logger_main.error(f"Error synchronizing time with {preferred_exchange} server: {str(e)}")
        log_exception(f"Error synchronizing time: {str(e)}", e)
        await async_exchange_fetcher.close(exchange)
        return []
    logger_main.debug(f"Loading markets for {preferred_exchange}")
    try:
        await asyncio.wait_for(async_exchange_fetcher.load_markets(exchange), timeout=60)
        logger_main.debug(f"Markets successfully loaded for {preferred_exchange}")
    except Exception as e:
        logger_main.error(f"Error loading markets for {preferred_exchange}: {str(e)}")
        log_exception(f"Error loading markets: {str(e)}", e)
        await async_exchange_fetcher.close(exchange)
        return []
    logger_main.debug(f"Checking symbol availability for {preferred_exchange}")
    symbols = [symbol for symbol in exchange.symbols if symbol.endswith('/USDT') and exchange.markets[symbol]['spot']]
    logger_main.debug(f"Found {len(symbols)} symbols to check: {symbols[:10]}...")
    filtered_symbols = []
    if preferred_exchange not in unavailable_symbols:
        unavailable_symbols[preferred_exchange] = set()
    try:
        balance = await asyncio.wait_for(async_exchange_fetcher.fetch_balance(exchange), timeout=10)
        logger_main.debug(f"Balance successfully fetched for {preferred_exchange}")
    except asyncio.TimeoutError as e:
        logger_main.error(f"Timeout fetching balance for {preferred_exchange}: {str(e)}")
        log_exception(f"Timeout fetching balance: {str(e)}", e)
        await async_exchange_fetcher.close(exchange)
        return []
    except ccxt.AuthenticationError as e:
        logger_main.error(f"Authentication error fetching balance for {preferred_exchange}: {str(e)}")
        await async_exchange_fetcher.close(exchange)
        return []
    except ccxt.BadRequest as e:
        logger_main.error(f"Invalid API key fetching balance for {preferred_exchange}: {str(e)}")
        await async_exchange_fetcher.close(exchange)
        return []
    except Exception as e:
        logger_main.error(f"Error fetching balance for {preferred_exchange}: {str(e)}")
        log_exception(f"Error fetching balance: {str(e)}", e)
        await async_exchange_fetcher.close(exchange)
        return []
    for i, symbol in enumerate(symbols):
        cache_key = f"{preferred_exchange}:{symbol}"
        if cache_key in symbol_check_cache:
            if symbol_check_cache[cache_key] == "unavailable":
                unavailable_symbols[preferred_exchange].add(symbol)
            else:
                filtered_symbols.append(symbol)
            continue
        try:
            logger_main.debug(f"Checking symbol {symbol} ({i+1}/{len(symbols)})")
            await asyncio.wait_for(
                async_exchange_fetcher.create_order(exchange, symbol, 'market', 'buy', 10.0, params={'test': True}),
                timeout=10
            )
            filtered_symbols.append(symbol)
            symbol_check_cache[cache_key] = "available"
        except asyncio.TimeoutError as e:
            logger_main.warning(f"Timeout checking symbol {symbol} on {preferred_exchange}: {str(e)}")
            unavailable_symbols[preferred_exchange].add(symbol)
            symbol_check_cache[cache_key] = "unavailable"
        except ccxt.AuthenticationError as e:
            logger_main.error(f"Authentication error checking symbol {symbol} for {preferred_exchange}: {str(e)}")
            break
        except ccxt.BadRequest as e:
            logger_main.warning(f"Symbol {symbol} unavailable for trading on {preferred_exchange}: {str(e)}")
            unavailable_symbols[preferred_exchange].add(symbol)
            symbol_check_cache[cache_key] = "unavailable"
        except Exception as e:
            logger_main.warning(f"Symbol {symbol} unavailable for trading on {preferred_exchange}: {str(e)}")
            unavailable_symbols[preferred_exchange].add(symbol)
            symbol_check_cache[cache_key] = "unavailable"
    filtered_symbols_cache[preferred_exchange] = filtered_symbols
    # Cache in Redis for 24 hours
    await redis_client.set_json(cache_key, filtered_symbols, expire=86400)
    logger_main.debug(f"Cached {len(filtered_symbols)} available symbols for {preferred_exchange}: {filtered_symbols[:10]}...")
    await async_exchange_fetcher.close(exchange)
    return filtered_symbols

__all__ = ['filter_symbols_for_exchange']
