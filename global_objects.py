from logging_setup import logger_main

SUPPORTED_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "XRP/USDT",
    "ADA/USDT"
]

logger_main.info("Global objects initialized with supported symbols")

__all__ = ['SUPPORTED_SYMBOLS']
