import aiohttp
import asyncio
from logging_setup import logger_main

async def validate_symbol(exchange_id, user_id, symbol, testnet=False, exchange=None):
    """Validates a symbol dynamically by checking exchange markets and activity."""
    if exchange is None:
        from exchange_factory import create_exchange
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return False
        should_close = True
    else:
        should_close = False

    try:
        # Try to load markets
        try:
            await exchange.load_markets()
            if symbol not in exchange.markets:
                logger_main.error(f"Symbol {symbol} not found in markets on {exchange_id}")
                return False

            # Check if symbol is active
            market = exchange.markets[symbol]
            if not market.get('active', True):
                logger_main.error(f"Symbol {symbol} is not active on {exchange_id}")
                return False

            # Fetch ticker to check volume and activity
            ticker = await exchange.fetch_ticker(symbol)
            if not ticker:
                logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange_id}")
                return False

            # Check trading volume (example threshold: 1000 units)
            volume = ticker.get('baseVolume', 0)
            min_volume_threshold = 1000
            if volume < min_volume_threshold:
                logger_main.warning(f"Symbol {symbol} has low trading volume ({volume} < {min_volume_threshold}) on {exchange_id}")
                return False

            logger_main.info(f"Symbol {symbol} validated successfully on {exchange_id}")
            return True
        except Exception as e:
            logger_main.warning(f"Failed to load markets for {exchange_id}: {e}, falling back to API check")

        # Fallback: Check symbol via public API
        async with aiohttp.ClientSession() as session:
            if exchange_id == "mexc":
                url = "https://api.mexc.com/api/v3/exchangeInfo"
            else:
                logger_main.error(f"No fallback API fetch implemented for {exchange_id}")
                return False

            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger_main.error(f"Failed to fetch exchange info from {exchange_id}: HTTP {response.status}")
                        return False
                    data = await response.json()
                    symbols = data.get('symbols', [])
                    logger_main.debug(f"Fetched exchange info for {exchange_id}: {len(symbols)} symbols")
                    for market in symbols:
                        if market['symbol'] == symbol:
                            if market['status'] == "1":
                                logger_main.info(f"Symbol {symbol} validated via API on {exchange_id}")
                                return True
                            else:
                                logger_main.debug(f"Symbol {symbol} not enabled on {exchange_id}: status={market['status']}")
                                return False
                    logger_main.debug(f"Symbol {symbol} not found in exchange info on {exchange_id}")
                    return False
            except Exception as e:
                logger_main.error(f"Error validating symbol {symbol} via API on {exchange_id}: {e}")
                return False
    except Exception as e:
        logger_main.error(f"Error validating symbol {symbol} on {exchange_id}: {e}")
        return False
    finally:
        if should_close and exchange is not None:
            logger_main.info(f"Closing exchange connection in symbol_handler for {exchange_id}")
            await exchange.close()

__all__ = ['validate_symbol']
