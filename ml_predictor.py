from logging_setup import logger_main
import torch
import pandas as pd
import numpy as np

async def predict(data, model, return_probs=False):
    """Makes predictions using the provided ML model."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if not isinstance(model, torch.nn.Module):
            logger_main.error(f"Model must be a torch.nn.Module, got {type(model)}")
            return None

        # Check input size
        expected_input_size = next(model.parameters()).shape[1]  # Get input size from the first layer
        if data.shape[1] != expected_input_size:
            logger_main.error(f"Input data has {data.shape[1]} features, but model expects {expected_input_size}")
            return None

        # Prepare data
        X = torch.tensor(data.values, dtype=torch.float32)
        model.eval()
        with torch.no_grad():
            predictions = model(X)
        probabilities = predictions.numpy().flatten()

        if return_probs:
            logger_main.info("Returning prediction probabilities")
            return probabilities

        # Convert probabilities to binary predictions
        binary_predictions = (probabilities > 0.5).astype(int)
        logger_main.info("Predictions made successfully")
        return binary_predictions
    except Exception as e:
        logger_main.error(f"Error making predictions: {e}")
        return None

__all__ = ['predict']
