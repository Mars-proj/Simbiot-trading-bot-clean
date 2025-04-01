from logging_setup import logger_main
from config_keys import MAX_POSITION_SIZE, MAX_POSITION_SIZE_PER_SYMBOL
import os

def check_limits(amount, leverage, open_trades):
    """Checks if the trade meets risk limits."""
    try:
        # Configurable limits
        max_position_size = float(os.getenv("MAX_POSITION_SIZE", MAX_POSITION_SIZE))
        max_position_size_per_symbol = float(os.getenv("MAX_POSITION_SIZE_PER_SYMBOL", MAX_POSITION_SIZE_PER_SYMBOL))

        # Calculate total position size
        total_position_size = sum(trade['amount'] * trade.get('leverage', 1) for trade in open_trades)
        new_position_size = amount * leverage
        total_position_size += new_position_size

        # Check total position size
        if total_position_size > max_position_size:
            logger_main.error(f"Total position size {total_position_size} exceeds limit {max_position_size}")
            return False

        # Check position size per symbol
        symbol_positions = {}
        for trade in open_trades:
            symbol = trade['symbol']
            symbol_positions[symbol] = symbol_positions.get(symbol, 0) + trade['amount'] * trade.get('leverage', 1)

        # Add new trade to symbol positions
        symbol_positions[symbol] = symbol_positions.get(symbol, 0) + new_position_size
        for symbol, position_size in symbol_positions.items():
            if position_size > max_position_size_per_symbol:
                logger_main.error(f"Position size for {symbol} ({position_size}) exceeds per-symbol limit {max_position_size_per_symbol}")
                return False

        logger_main.info(f"Trade limits check passed: total_position_size={total_position_size}, per_symbol_limits={symbol_positions}")
        return True
    except Exception as e:
        logger_main.error(f"Error checking trade limits: {e}")
        return False

__all__ = ['check_limits']
