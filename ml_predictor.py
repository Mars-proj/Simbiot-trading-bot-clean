from retraining_engine import RetrainEngine
from logging_setup import logger_main

# Create a global instance of RetrainEngine
ml_predictor = RetrainEngine()

# Log initialization inside a method that will be called after logger setup
def initialize_ml_predictor():
    logger_main.info("Initializing MLPredictor")
    ml_predictor.initialize_logging()

__all__ = ['ml_predictor', 'initialize_ml_predictor']
