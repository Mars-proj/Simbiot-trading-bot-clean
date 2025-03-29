import sys
import asyncio
from logging_setup import initialize_loggers, shutdown_loggers, logger_main
from config_keys import validate_api_keys
from config_settings import LOGGING_SETTINGS, validate_logging_settings
from config_notifications import validate_notification_settings
from trading_cycle import main
from trade_pool_core import TradePool
import global_objects

# Initialize loggers
print("Initializing loggers", file=sys.stderr)
if not initialize_loggers(LOGGING_SETTINGS):
    print("Failed to initialize loggers, exiting", file=sys.stderr)
    exit(1)
logger_main.info("Loggers initialized")

# Log redis_client initialization
logger_main.info("redis_client initialized from redis_initializer.py")

# Initialize global objects
logger_main.info("Creating global instance global_trade_pool")
global_objects.global_trade_pool = TradePool()

if __name__ == "__main__":
    try:
        # Validate settings
        logger_main.info("Validating settings")
        validate_api_keys(logger_main)
        validate_logging_settings(logger_main)
        validate_notification_settings(logger_main)

        # Check network connection
        logger_main.info("Checking network connection")
        import subprocess
        connected = False
        api_endpoints = ["api.mexc.com", "www.mexc.com"]
        for endpoint in api_endpoints:
            for attempt in range(3):
                try:
                    subprocess.check_call(["ping", "-c", "1", endpoint], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger_main.info(f"Network connection to {endpoint} successful (attempt {attempt + 1}/3)")
                    connected = True
                    break
                except subprocess.CalledProcessError as e:
                    logger_main.warning(f"Failed to connect to {endpoint} (attempt {attempt + 1}/3): {str(e)}")
                    if attempt == 2:
                        logger_main.error(f"Failed to establish network connection to {endpoint} after 3 attempts")
            if connected:
                break
        if not connected:
            logger_main.error("Failed to establish network connection to all endpoints, exiting")
            exit(1)

        # Create event loop
        logger_main.info("Creating event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger_main.info("Starting main trading cycle")
            loop.run_until_complete(main())
        finally:
            logger_main.info("Closing event loop")
            loop.close()
    finally:
        shutdown_loggers()
