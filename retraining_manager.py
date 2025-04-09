import joblib
import pandas as pd
from ml_data_preparer import prepare_data
from ml_model_trainer import train_lstm_model
from online_learning import OnlineLearning

class RetrainingManager:
    """
    Manage retraining of ML models with online learning.
    """

    def __init__(self, model_path="lstm_model.h5"):
        """
        Initialize the retraining manager.

        Args:
            model_path (str): Path to save the model (default: 'lstm_model.h5').
        """
        self.model_path = model_path
        self.online_learner = OnlineLearning()

    def retrain(self, data):
        """
        Retrain the ML model with new data.

        Args:
            data (pd.DataFrame): New OHLCV data.

        Returns:
            Trained model.
        """
        X, y = prepare_data(data)
        model = train_lstm_model(X, y, self.model_path)
        return model

    def online_update(self, x, y):
        """
        Update the online learning model with new data.

        Args:
            x (dict): Feature dictionary.
            y (int): Target value (1 for buy, 0 for sell).
        """
        self.online_learner.update(x, y)

    def online_predict(self, x):
        """
        Predict a trading signal using the online learning model.

        Args:
            x (dict): Feature dictionary.

        Returns:
            str: Trading signal ('buy' or 'sell').
        """
        return self.online_learner.predict(x)

    async def schedule_retraining(self, data_fetcher, symbols, timeframe, since, limit, interval=86400):
        """
        Schedule periodic retraining of the model.

        Args:
            data_fetcher: Function to fetch OHLCV data.
            symbols: List of symbols to retrain on.
            timeframe: Timeframe for OHLCV data.
            since: Timestamp to fetch from (in milliseconds).
            limit: Number of candles to fetch.
            interval: Retraining interval in seconds (default: 86400, i.e., 1 day).
        """
        while True:
            for symbol in symbols:
                data = await data_fetcher.fetch_ohlcv(symbol, timeframe, since, limit)
                self.retrain(data)
            await asyncio.sleep(interval)
