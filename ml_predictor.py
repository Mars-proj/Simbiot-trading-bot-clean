import joblib
from tensorflow.keras.models import load_model
import numpy as np
from features import extract_features, calculate_sma, calculate_rsi

class Predictor:
    """
    Predict trading signals using trained models and online learning.
    """

    def __init__(self, retraining_manager):
        """
        Initialize the predictor.

        Args:
            retraining_manager: RetrainingManager instance.
        """
        self.retraining_manager = retraining_manager

    async def predict_signal(self, symbol, data, model_type="lstm", model_path="lstm_model.h5"):
        """
        Predict a trading signal using a trained model or online learning.

        Args:
            symbol (str): Trading symbol.
            data (pd.DataFrame): OHLCV data.
            model_type (str): Type of model ('rf' for RandomForest, 'lstm' for LSTM, 'online' for online learning).
            model_path (str): Path to the trained model.

        Returns:
            str: Trading signal ('buy' or 'sell').
        """
        # Extract features
        features = await self.extract_features(data)

        if model_type == "rf":
            model = joblib.load(model_path)
            features_array = np.array(features).flatten().reshape(1, -1)
            prediction = model.predict(features_array)[0]
        elif model_type == "lstm":
            model = load_model(model_path)
            features_array = np.array([data['close'].values[-20:], data['volume'].values[-20:]]).T
            features_array = np.append(features_array, [features[-2:]], axis=0)
            features_array = features_array.reshape(1, features_array.shape[0], features_array.shape[1])
            prediction = model.predict(features_array)[0][0]
        else:  # Online learning
            features_dict = {
                "sma_20": features[0],
                "sma_50": features[1],
                "rsi": features[2],
                "volatility": features[3],
                "macd": features[4],
                "signal_line": features[5],
                "sharpe": features[6],
                "avg_return": features[7],
                "price_to_mean": features[8],
                "trend": features[9]
            }
            prediction = self.retraining_manager.online_predict(features_dict)
            return prediction

        return "buy" if prediction > 0.5 else "sell"

    async def extract_features(self, data):
        """
        Extract features for prediction.

        Args:
            data (pd.DataFrame): OHLCV data.

        Returns:
            list: Feature values.
        """
        features = extract_features(data)
        return features.tolist()
