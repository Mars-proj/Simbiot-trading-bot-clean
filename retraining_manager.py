from logging_setup import logger_main
import os
import time
import asyncio

class RetrainingManager:
    def __init__(self, retrain_interval=86400):  # Default: 24 hours
        self.retrain_interval = int(os.getenv("RETRAIN_INTERVAL", retrain_interval))
        self.last_retrain = 0

    async def retrain_model(self, data_loader, trainer, model_path):
        """Retrain the model with new data."""
        try:
            # Load data
            X_train, y_train, X_val, y_val = data_loader()
            if X_train is None or y_train is None or X_val is None or y_val is None:
                logger_main.error("Failed to load data for retraining")
                return False

            # Train the model
            success = trainer(X_train, y_train, X_val, y_val, input_size=X_train.shape[1], model_path=model_path)
            if not success:
                logger_main.error("Model retraining failed")
                return False

            self.last_retrain = int(time.time())
            logger_main.info(f"Model retrained successfully, saved to {model_path}")
            return True
        except Exception as e:
            logger_main.error(f"Error retraining model: {e}")
            return False

    async def schedule_retraining(self, data_loader, trainer, model_path):
        """Schedules periodic retraining of the model."""
        try:
            while True:
                current_time = int(time.time())
                if current_time - self.last_retrain >= self.retrain_interval:
                    logger_main.info("Starting scheduled model retraining")
                    await self.retrain_model(data_loader, trainer, model_path)
                await asyncio.sleep(3600)  # Check every hour
        except Exception as e:
            logger_main.error(f"Error in scheduled retraining: {e}")
            return False

__all__ = ['RetrainingManager']
