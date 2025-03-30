from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS
from ml_data_preparer import prepare_data
from ml_model_trainer import train_model

class RetrainingManager:
    """Manages the retraining of ML models."""
    def __init__(self, model_path):
        self.model_path = model_path

    async def retrain_model(self, data):
        """Retrains the ML model with new data."""
        try:
            if data is None or len(data) == 0:
                raise ValueError("Data for retraining is empty or None")

            # Prepare data for retraining
            prepared_data = await prepare_data(data, for_retraining=True)
            if prepared_data is None:
                logger_main.error("Failed to prepare data for retraining")
                return False

            # Train the model
            model = await train_model(prepared_data, self.model_path)
            if model is None:
                logger_main.error("Failed to retrain model")
                return False

            logger_main.info(f"Successfully retrained model at {self.model_path}")
            return True
        except FileNotFoundError as e:
            logger_main.error(f"Model file not found at {self.model_path}: {e}")
            return False
        except ValueError as e:
            logger_main.error(f"Invalid data for retraining: {e}")
            return False
        except Exception as e:
            logger_main.error(f"Error retraining model: {e}")
            return False

__all__ = ['RetrainingManager']
