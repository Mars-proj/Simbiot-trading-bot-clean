# retraining_manager.py
import asyncio
import traceback  # Добавили импорт
from logging_setup import logger_main

class RetrainingManager:
    def __init__(self, retrain_interval):
        self.retrain_interval = retrain_interval

    async def schedule_retraining(self, data_loader, train_model, model_path):
        while True:
            logger_main.info("Starting model retraining")
            try:
                X, y, _, _ = await data_loader()
                if X is None or y is None:
                    logger_main.error("Failed to load data for retraining")
                    await asyncio.sleep(self.retrain_interval)
                    continue
                train_model(X, y, model_path)
                logger_main.info("Model retraining completed successfully")
            except Exception as e:
                logger_main.error(f"Error in retraining schedule: {e}\n{traceback.format_exc()}")
            await asyncio.sleep(self.retrain_interval)
