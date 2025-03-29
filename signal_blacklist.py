from trade_blacklist import global_trade_blacklist
from logging_setup import logger_main

class SignalBlacklist:
    def __init__(self):
        self.blacklist = global_trade_blacklist

    def is_blacklisted(self, symbol):
        """Checks if a symbol is blacklisted for trading signals."""
        return symbol in self.blacklist

__all__ = ['SignalBlacklist']
