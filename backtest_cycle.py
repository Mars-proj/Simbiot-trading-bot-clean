from logging_setup import logger_main
from features import extract_features
import pandas as pd

def run_backtest_cycle(data, strategy_func, params):
    """
    Run a backtest cycle for a given strategy with specified parameters.

    Args:
        data: DataFrame with OHLCV data.
        strategy_func: Strategy function to test.
        params: Parameters for the strategy.

    Returns:
        dict: Backtest results.
    """
    logger_main.info(f"Starting backtest cycle with strategy {strategy_func.__name__}")
    
    # Extract features
    df = extract_features(data)
    
    # Apply strategy
    signals = strategy_func(df, **params)
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['returns'] * signals.shift(1)
    
    # Calculate cumulative returns
    cumulative_returns = (1 + df['strategy_returns']).cumprod()
    
    # Calculate metrics
    total_return = cumulative_returns.iloc[-1] - 1
    sharpe_ratio = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * (252 ** 0.5)  # Annualized
    
    results = {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'signals': signals
    }
    
    logger_main.info(f"Backtest completed: Total Return: {total_return}, Sharpe Ratio: {sharpe_ratio}")
    return results
