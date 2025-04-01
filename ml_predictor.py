import torch
import numpy as np
from logging_setup import logger_main
from ml_model_trainer import TradingModel

class MLPredictor:
    def __init__(self, model_path, input_size):
        """Initializes the ML predictor with a trained model."""
        try:
            self.model = TradingModel(input_size)
            self.model.load_state_dict(torch.load(model_path))
            self.model.eval()
            logger_main.info(f"Loaded ML model from {model_path}")
        except Exception as e:
            logger_main.error(f"Error loading ML model from {model_path}: {e}")
            raise

    def predict(self, features, return_probabilities=False):
        """Makes predictions using the trained model."""
        try:
            if not isinstance(features, np.ndarray):
                features = np.array(features)
            if features.shape[1] != self.model.layer1.in_features:
                logger_main.error(f"Input size mismatch: expected {self.model.layer1.in_features}, got {features.shape[1]}")
                return None

            # Convert to torch tensor
            features_tensor = torch.FloatTensor(features)

            # Make prediction
            with torch.no_grad():
                outputs = self.model(features_tensor)
                probabilities = outputs.numpy()
                predictions = (probabilities >= 0.5).astype(int)

            logger_main.info(f"Made predictions for {len(features)} samples")
            return probabilities if return_probabilities else predictions
        except Exception as e:
            logger_main.error(f"Error making predictions: {e}")
            return None

__all__ = ['MLPredictor']
