import torch
import numpy as np
from logging_setup import logger_main
from .ml_model_trainer import SimpleNN

class MLPredictor:
    def __init__(self, model_path, input_size):
        self.model_path = model_path
        self.input_size = input_size
        self.model = self._load_model()

    def _load_model(self):
        """Loads the trained model."""
        try:
            model = SimpleNN(self.input_size)
            model.load_state_dict(torch.load(self.model_path))
            model.eval()
            logger_main.info(f"Loaded model from {self.model_path}")
            return model
        except Exception as e:
            logger_main.error(f"Error loading model from {self.model_path}: {e}")
            raise

    def predict(self, features, return_probabilities=False):
        """Makes predictions using the loaded model, supports batch prediction."""
        try:
            # Validate input
            features = np.array(features, dtype=np.float32)
            if len(features.shape) == 1:
                features = features.reshape(1, -1)  # Reshape for single sample
            if features.shape[1] != self.input_size:
                logger_main.error(f"Invalid input size: expected {self.input_size}, got {features.shape[1]}")
                return None

            # Convert to tensor
            features_tensor = torch.FloatTensor(features)

            # Make prediction
            with torch.no_grad():
                outputs = self.model(features_tensor)
                probabilities = outputs.numpy()

            if return_probabilities:
                return probabilities.flatten() if probabilities.shape[0] == 1 else probabilities
            else:
                predictions = (probabilities > 0.5).astype(int)
                return predictions.flatten() if predictions.shape[0] == 1 else predictions
        except Exception as e:
            logger_main.error(f"Error making prediction: {e}")
            return None

__all__ = ['MLPredictor']
