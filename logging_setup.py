import logging
import os
from logging.handlers import RotatingFileHandler

# Configure main logger
logger_main = logging.getLogger('main')
logger_main.setLevel(logging.DEBUG)

# Add a basic console handler first to ensure logging works even if file handler fails
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger_main.addHandler(console_handler)

# Create file handler with error handling
log_file = "trading_bot.log"
try:
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger_main.addHandler(file_handler)
    logger_main.info("File handler added successfully")
except Exception as e:
    logger_main.error(f"Failed to create file handler for logging: {e}")

logger_main.info("All loggers initialized successfully")
