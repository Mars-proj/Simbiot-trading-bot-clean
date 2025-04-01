from logging_setup import logger_main

class SignalBlacklist:
    def __init__(self, blacklisted_symbols=None):
        """Initializes the signal blacklist with a list of symbols."""
        self.blacklist = set(blacklisted_symbols or [])

    def is_blacklisted(self, symbol):
        """Checks if a symbol is blacklisted."""
        try:
            if not symbol or not isinstance(symbol, str):
                logger_main.error(f"Invalid symbol for blacklist check: {symbol}")
                return False
            return symbol in self.blacklist
        except Exception as e:
            logger_main.error(f"Error checking blacklist for {symbol}: {e}")
            return False

__all__ = ['SignalBlacklist']
