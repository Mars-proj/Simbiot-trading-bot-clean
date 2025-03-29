# Dynamic criteria for symbol selection (system decides what to trade)
def get_dynamic_symbol_criteria(market_conditions=None):
    """Returns dynamic symbol selection criteria based on market conditions"""
    base_criteria = {
        'min_volatility': 0.05,  # Minimum annual volatility
        'min_volume': 500,       # Minimum average trading volume
        'max_spread': 0.005,     # Maximum spread (in percentage)
    }
    if market_conditions:
        avg_volatility = market_conditions.get('avg_volatility', 0.0)
        # Adjust criteria based on market volatility
        base_criteria['min_volatility'] = max(0.03, 0.05 * (1 - avg_volatility))  # Lower during high volatility
        base_criteria['min_volume'] = max(300, 500 * (1 - avg_volatility))        # Lower during high volatility
        base_criteria['max_spread'] = min(0.01, 0.005 * (1 + avg_volatility))     # Higher during high volatility
    return base_criteria

# Backtesting settings
def get_backtest_settings(market_conditions=None):
    """Returns dynamic backtesting settings based on market conditions"""
    base_settings = {
        'max_symbols': 100,      # Maximum number of symbols for backtesting
        'timeframe': '4h',       # Default timeframe for backtesting
        'limit': 500,            # Number of candles to load
    }
    if market_conditions:
        avg_volatility = market_conditions.get('avg_volatility', 0.0)
        # Adjust max_symbols and limit based on volatility
        base_settings['max_symbols'] = int(100 * (1 + avg_volatility))  # More symbols during high volatility
        base_settings['max_symbols'] = min(200, base_settings['max_symbols'])  # Cap at 200
        base_settings['limit'] = int(500 * (1 - avg_volatility / 2))    # Fewer candles during high volatility
        base_settings['limit'] = max(300, base_settings['limit'])       # Minimum 300 candles
        # Adjust timeframe based on volatility
        if avg_volatility > 0.1:  # High volatility
            base_settings['timeframe'] = '1h'  # Shorter timeframe for faster reaction
        elif avg_volatility < 0.05:  # Low volatility
            base_settings['timeframe'] = '12h'  # Longer timeframe for stability
    return base_settings

# Exchange connection settings
EXCHANGE_CONNECTION_SETTINGS = {
    'timeout': 60000,  # Timeout in milliseconds
    'rateLimit': 500,  # Rate limit in milliseconds (optimized for 10 Gbit/s network)
    'recvWindow': 30000,  # RecvWindow in milliseconds
}

# Cache settings for exchange manager
EXCHANGE_MANAGER_CACHE_SETTINGS = {
    'max_size': 1000,  # Maximum number of exchange instances in cache
    'ttl': 3600,  # Time-to-live for cache entries in seconds (1 hour)
}

# Logging settings
LOGGING_SETTINGS = {
    'level': 'DEBUG',        # Logging level: DEBUG, INFO, WARNING, ERROR
    'main_log_file': '/root/trading_bot/bot.log',
    'trade_pool_log_file': '/root/trading_bot/trade_pool.log',
    'debug_log_file': '/root/trading_bot/debug.log',
    'exceptions_log_file': '/root/trading_bot/exceptions.log',
    'max_log_size': 10485760,  # Maximum log file size in bytes (10 MB)
    'backup_count': 5,         # Number of backup log files
}

# Validate logging settings
def validate_logging_settings(logger_main):
    """Validates logging settings to ensure they are properly configured"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOGGING_SETTINGS['level'] not in valid_levels:
        logger_main.error(f"Invalid logging level: {LOGGING_SETTINGS['level']}. Must be one of {valid_levels}")
        raise ValueError(f"Invalid logging level: {LOGGING_SETTINGS['level']}")
    if LOGGING_SETTINGS['max_log_size'] <= 0:
        logger_main.error(f"Invalid max_log_size: {LOGGING_SETTINGS['max_log_size']}. Must be positive")
        raise ValueError(f"Invalid max_log_size: {LOGGING_SETTINGS['max_log_size']}")
    if LOGGING_SETTINGS['backup_count'] < 0:
        logger_main.error(f"Invalid backup_count: {LOGGING_SETTINGS['backup_count']}. Must be non-negative")
        raise ValueError(f"Invalid backup_count: {LOGGING_SETTINGS['backup_count']}")

__all__ = [
    'get_dynamic_symbol_criteria',
    'get_backtest_settings',
    'EXCHANGE_CONNECTION_SETTINGS',
    'EXCHANGE_MANAGER_CACHE_SETTINGS',
    'LOGGING_SETTINGS',
    'validate_logging_settings',
]
