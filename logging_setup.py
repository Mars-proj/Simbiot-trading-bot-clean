import logging
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO):
    """
    Setup logging configuration with rotation.

    Args:
        level: Logging level (default: logging.INFO).
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)  # 10 MB per file, 5 backups
        ]
    )
