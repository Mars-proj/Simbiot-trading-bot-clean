from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Инициализация Predictor
retraining_manager = RetrainingManager()
predictor = Predictor(retraining_manager)

class PredictionRequest(BaseModel):
    data: list

@app.post("/predict")
async def predict(request: PredictionRequest):
    """
    Endpoint to make predictions using the local model.

    Args:
        request: PredictionRequest object containing input data.

    Returns:
        dict: Prediction results.
    """
    logger.info("Received prediction request")
    
    try:
        # Преобразование входных данных в DataFrame
        df = pd.DataFrame(request.data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Выполнение предсказания
        prediction = predictor.predict(df)
        
        logger.info(f"Prediction result: {prediction}")
        return {"predictions": float(prediction)}
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        return {"error": str(e)}
