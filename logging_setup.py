import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# Определяем настройки логирования
logging_settings = {
    'main_log_file': '/root/trading_bot/logs/main.log',
    'debug_log_file': '/root/trading_bot/logs/debug.log',
    'exceptions_log_file': '/root/trading_bot/logs/exceptions.log',
    'trade_pool_log_file': '/root/trading_bot/logs/trade_pool.log',
    'level': 'DEBUG',  # Уровень логирования по умолчанию
    'max_log_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5  # Количество резервных копий логов
}

# Глобальные переменные для логгеров
logger_main = None
logger_debug = None
logger_exceptions = None
logger_trade_pool = None

def setup_logger(name, log_file, level, max_log_size, backup_count, filter_level=None):
    """Sets up a logger with file and console handlers"""
    try:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        # File handler with rotation
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_log_size,
            backupCount=backup_count
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        handler.setFormatter(formatter)
        # Если указан filter_level, добавляем фильтр для уровня логирования
        if filter_level:
            handler.addFilter(lambda record: record.levelno == filter_level)
        logger.addHandler(handler)
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        if filter_level:
            console_handler.addFilter(lambda record: record.levelno == filter_level)
        logger.addHandler(console_handler)
        return logger
    except Exception as e:
        print(f"Failed to set up logger {name}: {str(e)}", file=sys.stderr)
        return None

def initialize_loggers():
    """Initializes all loggers based on settings and returns success status"""
    global logger_main, logger_debug, logger_exceptions, logger_trade_pool
    try:
        # Create directories for all log files if they don't exist
        for log_file in [
            logging_settings['main_log_file'],
            logging_settings['debug_log_file'],
            logging_settings['exceptions_log_file'],
            logging_settings['trade_pool_log_file']
        ]:
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                print(f"Created directory for logs: {log_dir}", file=sys.stderr)
        # Set log level dynamically
        log_level = getattr(logging, logging_settings['level'], logging.DEBUG)
        # Initialize loggers
        # Логгер для INFO, WARNING и DEBUG (main.log)
        logger_main = setup_logger(
            'main',
            logging_settings['main_log_file'],
            log_level,
            logging_settings['max_log_size'],
            logging_settings['backup_count'],
            filter_level=None  # Убираем фильтр, чтобы видеть все уровни
        )
        # Логгер для DEBUG (debug.log)
        logger_debug = setup_logger(
            'debug',
            logging_settings['debug_log_file'],
            log_level,
            logging_settings['max_log_size'],
            logging_settings['backup_count'],
            filter_level=logging.DEBUG  # Только DEBUG
        )
        # Логгер для ERROR (exceptions.log)
        logger_exceptions = setup_logger(
            'exceptions',
            logging_settings['exceptions_log_file'],
            logging.ERROR,
            logging_settings['max_log_size'],
            logging_settings['backup_count'],
            filter_level=logging.ERROR  # Только ERROR
        )
        # Логгер для trade_pool (trade_pool.log)
        logger_trade_pool = setup_logger(
            'trade_pool',
            logging_settings['trade_pool_log_file'],
            log_level,
            logging_settings['max_log_size'],
            logging_settings['backup_count'],
            filter_level=logging.INFO  # INFO и выше для trade_pool
        )
        # Check if all loggers were initialized successfully
        if all([logger_main, logger_debug, logger_exceptions, logger_trade_pool]):
            print("All loggers initialized successfully", file=sys.stderr)
            return True
        else:
            print("Failed to initialize one or more loggers", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error initializing loggers: {str(e)}", file=sys.stderr)
        return False

def shutdown_loggers():
    """Properly shuts down all loggers"""
    global logger_main, logger_debug, logger_exceptions, logger_trade_pool
    if logger_main:
        logger_main.info("Shutting down loggers")
    for logger in [logger_main, logger_debug, logger_exceptions, logger_trade_pool]:
        if logger:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
    logging.shutdown()

# Автоматически инициализируем логгеры при импорте модуля
initialize_loggers()

__all__ = ['setup_logger', 'initialize_loggers', 'shutdown_loggers', 'logger_main', 'logger_debug', 'logger_exceptions', 'logger_trade_pool']
