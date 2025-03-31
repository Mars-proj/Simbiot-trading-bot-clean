import torch
from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS

class LocalModelAPI:
    """Local API for model inference using GPU."""
    def __init__(self, model_path: str):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            logger_main.info(f"Loaded model on {self.device} from {model_path}")
        except FileNotFoundError as e:
            logger_main.error(f"Model file not found at {model_path}: {e}")
            self.model = None
        except Exception as e:
            logger_main.error(f"Error loading model: {e}")
            self.model = None

    def predict(self, input_data: torch.Tensor) -> torch.Tensor:
        """Makes predictions using the model on GPU."""
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
            input_data = input_data.to(self.device)
            with torch.no_grad():
                output = self.model(input_data)
            logger_main.info("Performed inference on GPU")
            return output.cpu()
        except Exception as e:
            logger_main.error(f"Error during inference: {e}")
            return None

__all__ = ['LocalModelAPI']
