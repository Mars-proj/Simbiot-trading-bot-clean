import pandas as pd
from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES
import time

async def fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=100, testnet=False, as_dataframe=False):
    """Fetches OHLCV data for a symbol with pagination support."""
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

        # Fetch OHLCV data with pagination
        all_ohlcv = []
        since = None
        max_retries = 3
        retry_delay = 5  # seconds

        while True:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                    if not ohlcv:
                        logger_main.info(f"No more OHLCV data for {symbol} on {exchange_id}")
                        break

                    all_ohlcv.extend(ohlcv)

                    # Update since to the timestamp of the last candle
                    last_timestamp = ohlcv[-1][0]
                    since = last_timestamp + 1  # Move to the next timestamp

                    # Check if we received less data than requested (end of data)
                    if len(ohlcv) < limit:
                        logger_main.info(f"Reached end of OHLCV data for {symbol} on {exchange_id}")
                        break

                    # Avoid hitting rate limits
                    await asyncio.sleep(1)  # Small delay between requests
                    break  # Exit retry loop on success

                except Exception as e:
                    retry_count += 1
                    logger_main.warning(f"Error fetching OHLCV data for {symbol} on {exchange_id} (attempt {retry_count}/{max_retries}): {e}")
                    if retry_count == max_retries:
                        logger_main.error(f"Max retries reached for {symbol} on {exchange_id}")
                        return None
                    await asyncio.sleep(retry_delay)

            # Break the outer loop if no more data or end of data reached
            if not ohlcv or len(ohlcv) < limit:
                break

        if not all_ohlcv:
            logger_main.error(f"No OHLCV data returned for {symbol} on {exchange_id}")
            return None

        # Convert to DataFrame if requested
        if as_dataframe:
            data = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            logger_main.info(f"Fetched {len(data)} OHLCV data points for {symbol} on {exchange_id} as DataFrame")
            return data

        logger_main.info(f"Fetched {len(all_ohlcv)} OHLCV data points for {symbol} on {exchange_id}")
        return all_ohlcv
    except Exception as e:
        logger_main.error(f"Error fetching OHLCV data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_ohlcv']
