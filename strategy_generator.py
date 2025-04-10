import numpy as np
import logging

logger = logging.getLogger(__name__)

def generate_strategy_params(strategy_type, param_ranges):
    """
    Generate random parameters for a given strategy type.

    Args:
        strategy_type: Type of strategy ('sma', 'rsi', 'macd', 'bollinger', 'volume').
        param_ranges: Dict of parameter ranges for each strategy type.

    Returns:
        dict: Generated parameters.
    """
    logger.info(f"Generating parameters for {strategy_type} strategy")
    
    if strategy_type not in param_ranges:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    params = {}
    for param, (min_val, max_val) in param_ranges[strategy_type].items():
        params[param] = np.random.randint(min_val, max_val + 1)
    
    logger.info(f"Generated parameters: {params}")
    return params

if __name__ == "__main__":
    # Example usage
    param_ranges = {
        'sma': {'short_window': (10, 30), 'long_window': (40, 60)},
        'rsi': {'rsi_window': (10, 20), 'rsi_overbought': (60, 80), 'rsi_oversold': (20, 40)},
        'macd': {'short_window': (10, 15), 'long_window': (20, 30), 'signal_window': (5, 10)},
        'bollinger': {'window': (15, 25), 'num_std': (1, 3)},
        'volume': {'volume_window': (10, 30)}
    }
    
    params = generate_strategy_params('sma', param_ranges)
    print(params)
