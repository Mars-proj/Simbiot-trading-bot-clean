import asyncio
from logging_setup import logger_main
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import joblib

class RetrainingManager:
    def __init__(self, retrain_interval=86400):
        self.retrain_interval = retrain_interval
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    async def schedule_retraining(self, data_loader, train_model, model_path):
        """Schedules periodic retraining of the model."""
        while True:
            try:
                logger_main.info("Starting model retraining")
                # Загрузить данные
                X, y, _, _ = await data_loader()
                if X is None or y is None:
                    logger_main.error("Failed to load data for retraining")
                    await asyncio.sleep(self.retrain_interval)
                    continue

                # Обучить модель
                self.model.fit(X, y)
                logger_main.info("Model retrained successfully")

                # Сохранить модель
                joblib.dump(self.model, model_path)
                logger_main.info(f"Saved model to {model_path}")
            except Exception as e:
                logger_main.error(f"Error in retraining schedule: {e}")
            await asyncio.sleep(self.retrain_interval)

__all__ = ['RetrainingManager']
