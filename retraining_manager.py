import logging
import pandas as pd
from ml_predictor import Predictor
from ml_data_preparer import prepare_data

logger = logging.getLogger(__name__)

class RetrainingManager:
    def __init__(self):
        self.predictor = Predictor(self)

    def retrain(self, data):
        logger.info("Starting retraining process")
        prepared_data = prepare_data(data)
        
        # Convert prepared data to features and target for retraining
        X = prepared_data.drop(columns=['close'], errors='ignore')  # Features
        y = prepared_data['close'] if 'close' in prepared_data else None  # Target
        
        if y is None:
            logger.error("Target column 'close' not found in prepared data")
            return self.predictor
        
        # Retrain the model (assuming the model can be retrained incrementally)
        for i in range(len(X)):
            x_row = X.iloc[i].to_dict()
            y_value = y.iloc[i]
            self.predictor.model.fit([list(x_row.values())], [y_value], epochs=1, verbose=0)
        
        logger.info("Retraining completed")
        return self.predictor
