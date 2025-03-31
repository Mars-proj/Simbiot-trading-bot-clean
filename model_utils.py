from logging_setup import logger_main
import os
import torch

def validate_model_file(model_path):
    """Validates the existence and format of a model file."""
    try:
        if not os.path.exists(model_path):
            logger_main.error(f"Model file not found at {model_path}")
            return False

        # Try to load the model to validate its format
        try:
            model = torch.load(model_path, map_location=torch.device('cpu'))
            if not isinstance(model, torch.nn.Module):
                logger_main.error(f"File at {model_path} is not a valid PyTorch model")
                return False
        except Exception as e:
            logger_main.error(f"File at {model_path} is not a valid PyTorch model: {e}")
            return False

        logger_main.info(f"Model file validated: {model_path}")
        return True
    except Exception as e:
        logger_main.error(f"Error validating model file {model_path}: {e}")
        return False

__all__ = ['validate_model_file']
