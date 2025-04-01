import logging
import os
from logging.handlers import RotatingFileHandler

# Configure main logger
logger_main = logging.getLogger('main')
logger_main.setLevel(logging.DEBUG)  # Changed to DEBUG to see more details

# Create handlers
log_file = "/root/trading_bot/trading_bot.log"
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)  # 10MB per file, 5 backups
file_handler.setLevel(logging.DEBUG)  # Changed to DEBUG

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Changed to DEBUG

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger_main.addHandler(file_handler)
logger_main.addHandler(console_handler)

logger_main.info("All loggers initialized successfully")

__all__ = ['logger_main']
