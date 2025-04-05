import asyncio
from logging_setup import logger_main

class RetrainingManager:
    """Manages periodic retraining of the ML model."""
    def __init__(self, retrain_interval=86400):
        self.retrain_interval = retrain_interval
        self.running = False

    async def schedule_retraining(self, data_loader, train_model_func, model_path):
        """Schedules periodic retraining in the background."""
        if self.running:
            logger_main.warning("Retraining is already running, skipping new schedule")
            return

        self.running = True
        logger_main.info("Starting background retraining loop")
        try:
            while self.running:
                try:
                    logger_main.info("Starting model retraining")
                    X, y, _, _ = await data_loader()
                    if X is None or y is None:
                        logger_main.error("Failed to load data for retraining, skipping")
                        await asyncio.sleep(self.retrain_interval)
                        continue

                    logger_main.info(f"Training model with {len(X)} data points")
                    train_model_func(X, y, model_path)
                    logger_main.info("Model retraining completed successfully")

                except Exception as e:
                    logger_main.error(f"Error during retraining: {e}\n{traceback.format_exc()}")
                await asyncio.sleep(self.retrain_interval)
        finally:
            self.running = False
            logger_main.info("Stopped background retraining loop")

    def stop(self):
        """Stops the retraining loop."""
        self.running = False
