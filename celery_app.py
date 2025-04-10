import asyncio
from celery import Celery
from logging_setup import logger_main
from exchange_detector import ExchangeDetector
from exchange_pool import ExchangePool
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
from signal_blacklist import SignalBlacklist
from strategy_manager import StrategyManager
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np

app = Celery('trading_bot', broker='amqp://guest:guest@localhost/', backend='rpc://')
app.conf.broker_connection_retry_on_startup = True

@app.task
def process_user_task(user, credentials, since, limit, timeframe, symbol_batch=None):
    """
    Process trading task for a user.

    Args:
        user: User ID.
        credentials: User credentials (API keys).
        since: Timestamp to fetch OHLCV data from.
        limit: Number of OHLCV candles to fetch.
        timeframe: Timeframe for OHLCV data.
        symbol_batch: List of symbols to process (optional, if None, fetch all available symbols).
    """
    logger_main.info(f"Processing task for user {user}")
    
    async def process_user_async():
        # Создаём ExchangePool и ExchangeDetector внутри задачи
        exchange_pool = ExchangePool()
        detector = ExchangeDetector()
        
        # Detect exchange
        exchange = await detector.detect_exchange(credentials['api_key'], credentials['api_secret'])
        logger_main.info(f"Detected exchange: {exchange}")
        if not exchange:
            logger_main.error(f"Failed to detect exchange for user {user}")
            await detector.close()
            await exchange_pool.close()
            return
        if not hasattr(exchange, 'fetch_ohlcv'):
            logger_main.error(f"Exchange object is invalid: {exchange}")
            await detector.close()
            await exchange_pool.close()
            return
        
        # Загружаем доступные рынки для биржи
        try:
            markets = await exchange.load_markets()
            available_symbols = list(markets.keys())
            logger_main.info(f"Available symbols on {exchange.id}: {available_symbols[:10]}... (first 10 shown)")
        except Exception as e:
            logger_main.error(f"Failed to load markets for {exchange.id}: {str(e)}")
            await detector.close()
            await exchange_pool.close()
            return

        # Если symbol_batch не указан, выбираем все доступные символы
        if symbol_batch is None:
            symbol_batch = available_symbols
            logger_main.info(f"Fetched all available symbols: {len(symbol_batch)} symbols")

        # Адаптируем символы для биржи
        adapted_symbol_batch = []
        for symbol in symbol_batch:
            # Преобразуем символ в формат биржи (например, BTC/USDT -> BTC_USDT для MEXC)
            adapted_symbol = symbol.replace('/', '_')  # MEXC использует BTC_USDT
            if adapted_symbol in available_symbols:
                adapted_symbol_batch.append(adapted_symbol)
            else:
                # Пробуем обратный формат (например, BTC_USDT -> BTC/USDT)
                alt_symbol = symbol.replace('_', '/')
                if alt_symbol in available_symbols:
                    adapted_symbol_batch.append(alt_symbol)
                else:
                    logger_main.warning(f"Symbol {symbol} not found on {exchange.id}, skipping")
                    continue

        if not adapted_symbol_batch:
            logger_main.error(f"No valid symbols found for {exchange.id}")
            await detector.close()
            await exchange_pool.close()
            return

        logger_main.info(f"Adapted symbols for {exchange.id}: {adapted_symbol_batch[:10]}... (first 10 shown)")

        # Анализ и выбор токенов на основе объёма и волатильности
        selected_symbols = []
        for symbol in adapted_symbol_batch:
            try:
                # Получаем тикер для анализа объёма
                ticker = await exchange.fetch_ticker(symbol)
                volume = ticker.get('baseVolume', 0)
                if volume < 1000:  # Пропускаем токены с низким объёмом
                    logger_main.debug(f"Skipping {symbol} due to low volume: {volume}")
                    continue

                # Получаем OHLCV данные для анализа волатильности
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Вычисляем волатильность (стандартное отклонение процентного изменения цены)
                df['returns'] = df['close'].pct_change()
                volatility = df['returns'].std() * np.sqrt(len(df))
                if volatility < 0.01:  # Пропускаем токены с низкой волатильностью
                    logger_main.debug(f"Skipping {symbol} due to low volatility: {volatility}")
                    continue

                selected_symbols.append(symbol)
                logger_main.info(f"Selected {symbol} for trading: volume={volume}, volatility={volatility}")
            except Exception as e:
                logger_main.error(f"Error analyzing {symbol}: {str(e)}")
                continue

        if not selected_symbols:
            logger_main.error(f"No symbols selected after analysis for {exchange.id}")
            await detector.close()
            await exchange_pool.close()
            return

        logger_main.info(f"Selected symbols for trading: {selected_symbols}")

        # Initialize components
        retraining_manager = RetrainingManager()
        predictor = Predictor(retraining_manager)
        signal_blacklist = SignalBlacklist()
        strategy_manager = StrategyManager()
        
        # Fetch OHLCV data for each selected symbol
        for symbol in selected_symbols:
            if signal_blacklist.is_blacklisted(symbol):
                logger_main.info(f"Skipping blacklisted symbol {symbol} for user {user}")
                continue
            
            try:
                logger_main.info(f"Fetching OHLCV data for {symbol}")
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                logger_main.info(f"Fetched OHLCV data for {symbol}: {len(df)} candles")
                
                # Generate strategy parameters
                strategy_type = 'sma'  # Example: use SMA strategy
                params = strategy_manager.generate_params(strategy_type)
                strategy_func = strategy_manager.get_strategy(strategy_type)
                
                # Apply strategy
                signals = strategy_func(df, **params)
                logger_main.info(f"Generated signals for {symbol}: {signals.tail()}")
                
                # Make prediction
                prediction = predictor.predict(df)
                logger_main.info(f"Prediction for {symbol}: {prediction}")
                
                # Execute trade based on signal
                latest_signal = signals.iloc[-1]
                if latest_signal == 1:  # Buy signal
                    logger_main.info(f"Executing buy order for {symbol} for user {user}")
                    order = await exchange.create_market_buy_order(symbol, 0.01)  # Example: buy 0.01 units
                    logger_main.info(f"Buy order executed: {order}")
                elif latest_signal == -1:  # Sell signal
                    logger_main.info(f"Executing sell order for {symbol} for user {user}")
                    order = await exchange.create_market_sell_order(symbol, 0.01)  # Example: sell 0.01 units
                    logger_main.info(f"Sell order executed: {order}")
                
                # Retrain model with new data
                retraining_manager.retrain(df)
                logger_main.info(f"Retrained model with data for {symbol}")
                
            except Exception as e:
                logger_main.error(f"Error processing {symbol} for user {user}: {str(e)}")
                continue
        
        await detector.close()
        await exchange_pool.close()
        logger_main.info(f"Completed task for user {user}")
    
    # Запускаем асинхронную функцию внутри синхронной задачи
    asyncio.run(process_user_async())
