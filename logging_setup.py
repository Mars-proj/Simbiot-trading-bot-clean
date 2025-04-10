import logging

# Configure the main logger for the application
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Main logger for the application
logger_main = logging.getLogger(__name__)

# Configure a separate logger for notifications
notification_logger = logging.getLogger('notification')
notification_handler = logging.StreamHandler()
notification_handler.setLevel(logging.INFO)
notification_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
notification_handler.setFormatter(notification_formatter)
notification_logger.addHandler(notification_handler)
