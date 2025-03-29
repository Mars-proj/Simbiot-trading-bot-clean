import pandas as pd
import numpy as np
import asyncio
import pandas_ta as ta
from utils import logger_main, log_exception
from backtester import Backtester
from ml_data_preparer_utils import backtest_cache, MAX_CONCURRENT_REQUESTS, REQUEST_DELAY, semaphore
from async_ohlcv_fetcher import AsyncOHLCVFetcher
from config import get_dynamic_symbol_criteria, get_backtest_settings
from global_objects import redis_client

class MLDataPreparer:
    def __init__(self):
        self.concurrent_requests = MAX_CONCURRENT_REQUESTS  # Dynamic limit for requests
        self.error_count = 0  # Error counter for adaptive management
        self.async_fetcher = AsyncOHLCVFetcher(exchange_manager=None, semaphore=semaphore)

    def initialize_logging(self):
        """Initializes logging for MLDataPreparer and its dependencies"""
        logger_main.info("Initializing MLDataPreparer")
        self.async_fetcher.initialize_logging()

    async def fetch_ohlcv_with_limit(self, exchange, symbol, timeframe, limit):
        """Fetches OHLCV data with rate limiting"""
        async with semaphore:
            try:
                # Check Redis cache
                cache_key = f"ohlcv:{exchange.id}:{symbol}:{timeframe}:{limit}"
                cached_data = await redis_client.get_json(cache_key)
                if cached_data is not None:
                    logger_main.info(f"Using cached OHLCV data for {symbol}")
                    return cached_data
                logger_main.info(f"Fetching OHLCV data for {symbol} (timeframe={timeframe}, limit={limit})")
                ohlcv = await self.async_fetcher.fetch_ohlcv(exchange, symbol, timeframe, limit)
                if ohlcv is None:
                    raise Exception("Failed to fetch OHLCV data")
                logger_main.info(f"Successfully fetched OHLCV data for {symbol}: {len(ohlcv)} records")
                # Cache in Redis for 1 hour
                await redis_client.set_json(cache_key, ohlcv, expire=3600)
                # Reset error counter
                self.error_count = max(0, self.error_count - 1)
                await asyncio.sleep(REQUEST_DELAY)  # Delay after each request
                return ohlcv
            except Exception as e:
                logger_main.warning(f"Error fetching data for {symbol}: {str(e)}")
                log_exception(f"Error fetching OHLCV for {symbol}: {str(e)}", e)
                # Increase error counter
                self.error_count += 1
                # Adaptively reduce request limit
                if self.error_count > 5:
                    self.concurrent_requests = max(1, self.concurrent_requests - 1)
                    logger_main.info(f"Reducing concurrent request limit to {self.concurrent_requests} due to errors")
                    self.error_count = 0
                return None

    async def calculate_indicators(self, df):
        """Calculates technical indicators for a DataFrame"""
        try:
            df['rsi'] = ta.rsi(df['close'], length=14)
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            bb = ta.bbands(df['close'], length=20)
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_middle'] = bb['BBM_20_2.0']
            df['bb_lower'] = bb['BBL_20_2.0']
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
            return df
        except Exception as e:
            logger_main.error(f"Error calculating indicators: {str(e)}")
            log_exception(f"Error calculating indicators: {str(e)}", e)
            return df

    async def prepare_backtest_data(self, exchange, timeframe=None, limit=None, unavailable_symbols=None, market_conditions=None):
        """Prepares data for training using backtesting"""
        logger_main.info("Preparing data for training via backtesting")
        try:
            exchange_id = exchange.id
            # Use dynamic backtest settings
            backtest_settings = get_backtest_settings(market_conditions)
            timeframe = timeframe or backtest_settings['timeframe']
            limit = limit or backtest_settings['limit']
            max_symbols = backtest_settings['max_symbols']
            # Check Redis cache for backtest data
            cache_key = f"backtest_data:{exchange_id}:{timeframe}:{limit}"
            cached_data = await redis_client.get_json(cache_key)
            if cached_data is not None:
                logger_main.info(f"Using cached backtest data for {exchange_id}")
                return pd.DataFrame(cached_data)
            # Load market symbols
            logger_main.info("Loading markets for exchange")
            await asyncio.to_thread(exchange.load_markets)
            if not hasattr(exchange, 'symbols') or exchange.symbols is None:
                logger_main.error(f"Failed to load markets for exchange {exchange_id}, exchange.symbols is None")
                return None
            symbols = [symbol for symbol in exchange.symbols if symbol.endswith('/USDT') and exchange.markets[symbol]['spot']]
            logger_main.info(f"Found {len(symbols)} symbols before filtering: {symbols[:10]}...")
            # Exclude unavailable symbols
            if unavailable_symbols is not None:
                unavailable = unavailable_symbols.get(exchange_id, set())
                symbols = [symbol for symbol in symbols if symbol not in unavailable]
                logger_main.info(f"After excluding unavailable symbols for {exchange_id}: {len(symbols)} symbols")
            # Fetch OHLCV data for filtering
            symbol_metrics = []
            tasks = []
            for symbol in symbols:
                tasks.append(self.fetch_ohlcv_with_limit(exchange, symbol, timeframe, 30))
            ohlcv_results = await asyncio.gather(*tasks, return_exceptions=True)
            # Use dynamic symbol criteria
            criteria = get_dynamic_symbol_criteria(market_conditions)
            for symbol, ohlcv in zip(symbols, ohlcv_results):
                try:
                    if ohlcv is None or isinstance(ohlcv, Exception):
                        logger_main.warning(f"Error fetching data for {symbol}: {str(ohlcv)}")
                        continue
                    if not ohlcv:
                        logger_main.warning(f"Empty OHLCV data for {symbol}")
                        continue
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    logger_main.debug(f"OHLCV data for {symbol} (first 5 rows): {df.head().to_dict()}")
                    df['returns'] = df['close'].pct_change()
                    volatility = df['returns'].rolling(window=20).std().iloc[-1] * np.sqrt(252) if not df['returns'].empty else 0
                    avg_volume = df['volume'].mean()
                    # Filter by dynamic criteria
                    if volatility < criteria['min_volatility'] or avg_volume < criteria['min_volume']:
                        logger_main.info(f"Symbol {symbol} excluded: low volatility ({volatility:.4f}) or volume ({avg_volume:.2f})")
                        continue
                    # Check spread (approximate via last candle)
                    bid = df['close'].iloc[-1] * (1 - criteria['max_spread'] / 2)
                    ask = df['close'].iloc[-1] * (1 + criteria['max_spread'] / 2)
                    spread = (ask - bid) / bid
                    if spread > criteria['max_spread']:
                        logger_main.info(f"Symbol {symbol} excluded: spread ({spread:.4f}) exceeds maximum ({criteria['max_spread']})")
                        continue
                    # Additional trend check
                    df['sma_short'] = df['close'].rolling(window=10).mean()
                    df['sma_long'] = df['close'].rolling(window=20).mean()
                    trend_score = 1 if df['sma_short'].iloc[-1] > df['sma_long'].iloc[-1] else -1 if df['sma_short'].iloc[-1] < df['sma_long'].iloc[-1] else 0
                    # Combined score: volume * volatility * (1 + |trend_score|)
                    combined_score = avg_volume * volatility * (1 + abs(trend_score))
                    logger_main.debug(f"For {symbol}: volatility={volatility:.4f}, avg_volume={avg_volume:.2f}, trend_score={trend_score}, combined_score={combined_score:.2f}")
                    symbol_metrics.append((symbol, combined_score, volatility, avg_volume))
                except Exception as e:
                    logger_main.warning(f"Error processing symbol {symbol}: {str(e)}")
                    log_exception(f"Error processing symbol {symbol}: {str(e)}", e)
                    continue
            logger_main.info(f"Collected {len(symbol_metrics)} symbols in symbol_metrics")
            # Sort by combined score and select top symbols
            symbol_metrics.sort(key=lambda x: x[1], reverse=True)
            selected_symbols = [metric[0] for metric in symbol_metrics[:max_symbols]]
            logger_main.info(f"Selected {len(selected_symbols)} symbols for backtesting: {selected_symbols}")
            # Initialize backtester
            backtester = Backtester(initial_balance=1000, commission_rate=0.001, slippage_rate=0.001)
            strategies = ['trend', 'momentum', 'volatility', 'volume', 'support_resistance']
            data_list = []
            symbol_data = {}  # Cache for OHLCV data and indicators
            processed_symbols = 0  # Counter for processed symbols
            # Fetch OHLCV data for all symbols in parallel
            tasks = []
            for symbol in selected_symbols:
                tasks.append(self.fetch_ohlcv_with_limit(exchange, symbol, timeframe, limit))
            ohlcv_results = await asyncio.gather(*tasks, return_exceptions=True)
            # Calculate indicators in parallel
            indicator_tasks = []
            for symbol, ohlcv in zip(selected_symbols, ohlcv_results):
                try:
                    if ohlcv is None or isinstance(ohlcv, Exception):
                        logger_main.warning(f"Failed to fetch OHLCV data for {symbol}: {str(ohlcv)}")
                        continue
                    if not ohlcv:
                        logger_main.warning(f"Empty OHLCV data for {symbol}")
                        continue
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    logger_main.debug(f"OHLCV data for {symbol}: {df[['timestamp', 'close']].head().to_dict()}")
                    df = df.dropna()
                    if len(df) < 50:  # Minimum data requirement
                        logger_main.warning(f"Insufficient data for {symbol} after removing NaN")
                        continue
                    indicator_tasks.append(self.calculate_indicators(df))
                    symbol_data[symbol] = df
                except Exception as e:
                    logger_main.warning(f"Error processing OHLCV for {symbol}: {str(e)}")
                    log_exception(f"Error processing OHLCV for {symbol}: {str(e)}", e)
                    continue
            # Calculate indicators in parallel
            indicator_results = await asyncio.gather(*indicator_tasks, return_exceptions=True)
            for symbol, df in zip(symbol_data.keys(), indicator_results):
                if isinstance(df, Exception):
                    logger_main.warning(f"Error calculating indicators for {symbol}: {str(df)}")
                    continue
                symbol_data[symbol] = df
                processed_symbols += 1
                logger_main.info(f"Processed {processed_symbols}/{len(selected_symbols)} symbols (remaining: {len(selected_symbols) - processed_symbols})")
            # Perform backtesting for each strategy
            for symbol in symbol_data:
                df = symbol_data[symbol]
                for strategy in strategies:
                    logger_main.info(f"Running backtest for {symbol} with strategy {strategy}")
                    result = backtester.run_backtest(df, strategy, trade_amount_percentage=0.1)
                    if not result:
                        logger_main.warning(f"Backtest for {symbol} ({strategy}) returned no results")
                        continue
                    trades = result.get('trades', [])
                    logger_main.info(f"Retrieved {len(trades)} trades from backtest for {symbol} ({strategy})")
                    for trade in trades:
                        entry_time = trade['entry_time']
                        trade_data = df[df['timestamp'] <= entry_time].tail(1)
                        if trade_data.empty:
                            logger_main.info(f"No data for trade at {entry_time} for {symbol}")
                            continue
                        trade_data = trade_data.copy()
                        trade_data['amount'] = trade['amount']
                        trade_data['trade_success'] = 1 if trade['profit'] > 0 else 0
                        trade_data['strategy'] = strategy
                        trade_data['symbol'] = symbol
                        data_list.append(trade_data)
            if not data_list:
                logger_main.warning("No data prepared after backtesting")
                return None
            final_df = pd.concat(data_list, ignore_index=True)
            logger_main.info(f"Prepared {len(final_df)} data points for training")
            # Cache the final DataFrame in Redis
            await redis_client.set_json(cache_key, final_df.to_dict('records'), expire=3600)
            return final_df
        except Exception as e:
            logger_main.error(f"Error preparing backtest data: {str(e)}")
            log_exception(f"Error preparing backtest data: {str(e)}", e)
            return None
