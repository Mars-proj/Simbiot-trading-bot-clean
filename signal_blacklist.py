from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS

class SignalBlacklist:
    """Manages a blacklist of symbols."""
    def __init__(self, blacklisted_symbols=None):
        self.blacklisted_symbols = blacklisted_symbols if blacklisted_symbols is not None else ["XRP/USDT"]
        logger_main.info(f"Initialized SignalBlacklist with blacklisted symbols: {self.blacklisted_symbols}")

    def is_blacklisted(self, symbol: str) -> bool:
        """Checks if a symbol is blacklisted."""
        try:
            if symbol in self.blacklisted_symbols:
                logger_main.info(f"Symbol {symbol} is blacklisted")
                return True
            return False
        except Exception as e:
            logger_main.error(f"Error checking blacklist for {symbol}: {e}")
            return False

__all__ = ['SignalBlacklist']
