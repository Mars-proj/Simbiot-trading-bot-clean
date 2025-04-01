from logging_setup import logger_main
import torch

def validate_model(model_path):
    """Validates that the model file exists and is a valid PyTorch model."""
    try:
        if not os.path.exists(model_path):
            logger_main.error(f"Model file does not exist: {model_path}")
            return False

        # Attempt to load the model state dict
        state_dict = torch.load(model_path)
        if not isinstance(state_dict, dict):
            logger_main.error(f"Model file {model_path} is not a valid PyTorch state dict")
            return False

        logger_main.info(f"Model file {model_path} validated successfully")
        return True
    except Exception as e:
        logger_main.error(f"Error validating model file {model_path}: {e}")
        return False

__all__ = ['validate_model']
