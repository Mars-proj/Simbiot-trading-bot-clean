from celery import Celery
from logging_setup import logger_main
from exchange_detector import ExchangeDetector
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
from signal_blacklist import SignalBlacklist
from strategy_manager import StrategyManager
import ccxt.async_support as ccxt
import pandas as pd

app = Celery('trading_bot', broker='amqp://guest:guest@localhost/', backend='rpc://')

@app.task
def process_user_task(user, credentials, since, limit, timeframe, symbol_batch, exchange_pool, detector):
    """
    Process trading task for a user.

    Args:
        user: User ID.
        credentials: User credentials (API keys).
        since: Timestamp to fetch OHLCV data from.
        limit: Number of OHLCV candles to fetch.
        timeframe: Timeframe for OHLCV data.
        symbol_batch: List of symbols to process.
        exchange_pool: ExchangePool instance (not used, replaced by detector).
        detector: ExchangeDetector instance.
    """
    logger_main.info(f"Processing task for user {user}")
    
    # Detect exchange
    exchange = await detector.detect_exchange(credentials['api_key'], credentials['api_secret'])
    if not exchange:
        logger_main.error(f"Failed to detect exchange for user {user}")
        return
    
    # Initialize components
    retraining_manager = RetrainingManager()
    predictor = Predictor(retraining_manager)
    signal_blacklist = SignalBlacklist()
    strategy_manager = StrategyManager()
    
    # Fetch OHLCV data for each symbol
    for symbol in symbol_batch:
        if signal_blacklist.is_blacklisted(symbol):
            logger_main.info(f"Skipping blacklisted symbol {symbol} for user {user}")
            continue
        
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Generate strategy parameters
            strategy_type = 'sma'  # Example: use SMA strategy
            params = strategy_manager.generate_params(strategy_type)
            strategy_func = strategy_manager.get_strategy(strategy_type)
            
            # Apply strategy
            signals = strategy_func(df, **params)
            
            # Make prediction
            prediction = predictor.predict(df)
            logger_main.info(f"Prediction for {symbol}: {prediction}")
            
            # Execute trade based on signal (example logic)
            latest_signal = signals.iloc[-1]
            if latest_signal == 1:  # Buy signal
                logger_main.info(f"Executing buy order for {symbol} for user {user}")
                # Add trade execution logic here
            elif latest_signal == -1:  # Sell signal
                logger_main.info(f"Executing sell order for {symbol} for user {user}")
                # Add trade execution logic here
            
            # Retrain model with new data
            retraining_manager.retrain(df)
            
        except Exception as e:
            logger_main.error(f"Error processing {symbol} for user {user}: {str(e)}")
            continue
    
    await detector.close()
    logger_main.info(f"Completed task for user {user}")
