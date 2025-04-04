# retraining_manager.py
import asyncio
from logging_setup import logger_main

class RetrainingManager:
    def __init__(self, retrain_interval=86400):
        self.retrain_interval = retrain_interval

    async def schedule_retraining(self, data_loader, train_model, model_path):
        """
        Schedules model retraining at specified intervals.
        Args:
            data_loader: Function to load training data
            train_model: Function to train the model
            model_path: Path to save the trained model (not used in train_model call)
        """
        while True:
            try:
                logger_main.info("Starting retraining process")
                X, y, _, _ = await data_loader()
                if X is None or y is None:
                    logger_main.error("Failed to load data for retraining")
                    await asyncio.sleep(self.retrain_interval)
                    continue
                logger_main.info(f"Training model with {len(X)} data points")
                train_model(X, y)  # Убираем model_path из вызова
                logger_main.info("Model retraining completed successfully")
            except Exception as e:
                logger_main.error(f"Error in retraining schedule: {e}")
            await asyncio.sleep(self.retrain_interval)
