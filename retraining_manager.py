import asyncio
from logging_setup import logger_main

class RetrainingManager:
    def __init__(self, retrain_interval=86400):
        self.retrain_interval = retrain_interval  # Default: 24 hours

    async def schedule_retraining(self, data_loader, train_function, model_path):
        """Schedules periodic retraining of the ML model."""
        try:
            while True:
                logger_main.info("Starting model retraining")
                X_train, y_train, X_test, y_test = await data_loader()
                if X_train is None or y_train is None:
                    logger_main.error("Failed to load data for retraining")
                    await asyncio.sleep(self.retrain_interval)
                    continue

                model, metrics = train_function(X_train, y_train, model_path)
                if model is None:
                    logger_main.error("Model retraining failed")
                else:
                    logger_main.info(f"Model retrained successfully: {metrics}")

                await asyncio.sleep(self.retrain_interval)
        except Exception as e:
            logger_main.error(f"Error in retraining schedule: {e}")
            return False

__all__ = ['RetrainingManager']
