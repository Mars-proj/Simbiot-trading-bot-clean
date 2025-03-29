import asyncio
import pandas as pd
from logging_setup import logger_main
from utils import log_exception
from symbol_filter import filter_symbols
from ohlcv_fetcher import fetch_ohlcv_with_cache, symbol_data_cache
from trade_executor_signals import execute_trade

async def process_symbols(exchange, user_id, ex_name, trade_executor, symbols=None):
    logger_main.info(f"Processing symbols for {user_id} on {ex_name}")
    try:
        # If symbols are not provided, filter them dynamically
        if not symbols:
            symbols = await filter_symbols(exchange, user_id=user_id)
        logger_main.info(f"Found {len(symbols)} symbols after filtering for {user_id} on {ex_name}: {symbols[:10]}...")
        # Fetch OHLCV data for all symbols in parallel
        ohlcv_tasks = []
        for symbol in symbols:
            cache_key = f"{ex_name}:{symbol}:4h:500"
            if cache_key in symbol_data_cache:
                logger_main.debug(f"Using cached OHLCV data for {symbol}")
                ohlcv_tasks.append(asyncio.ensure_future(asyncio.sleep(0, result=(symbol, symbol_data_cache[cache_key]))))
            else:
                ohlcv_tasks.append(asyncio.ensure_future(fetch_ohlcv_with_cache(exchange, symbol, '4h', 500, cache_key)))
        ohlcv_results = await asyncio.gather(*ohlcv_tasks, return_exceptions=True)
        symbol_data = {}
        for result in ohlcv_results:
            if isinstance(result, (Exception, asyncio.CancelledError)):
                logger_main.warning(f"Error fetching OHLCV: {str(result)}")
                continue
            symbol, ohlcv = result
            if ohlcv is None:
                logger_main.warning(f"Failed to fetch OHLCV for {symbol}")
                continue
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            symbol_data[symbol] = df
        # Process symbols in parallel
        trade_tasks = []
        total_symbols = len(symbol_data)
        processed_symbols = 0
        for symbol in symbol_data:
            trade_tasks.append(asyncio.ensure_future(execute_trade(trade_executor, exchange, symbol, user_id)))
            processed_symbols += 1
            progress = (processed_symbols / total_symbols) * 100
            logger_main.debug(f"Scheduled processing of {symbol} ({processed_symbols}/{total_symbols} symbols, progress: {progress:.2f}%)")
        trade_results = await asyncio.gather(*trade_tasks, return_exceptions=True)
        for symbol, result in zip(symbol_data.keys(), trade_results):
            if isinstance(result, Exception):
                logger_main.error(f"Error processing symbol {symbol} for {user_id}: {str(result)}")
                log_exception(f"Error processing symbol {symbol}: {str(result)}", result)
    except Exception as e:
        logger_main.error(f"Error processing symbols for {user_id} on {ex_name}: {str(e)}")
        log_exception(f"Error processing symbols: {str(e)}", e)

__all__ = ['process_symbols']
