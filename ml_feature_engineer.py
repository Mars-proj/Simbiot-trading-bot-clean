import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from utils import logger_main, log_exception

class MLFeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.features = ['close', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_middle', 'bb_lower', 'volatility', 'amount']
        self.target_success = 'trade_success'
        self.target_price = 'future_close'
        self.scaler_cache = {}  # Кэш для нормализованных данных
        logger_main.info("Инициализация MLFeatureEngineer")

    def extract_features(self, data):
        """Извлекает признаки и целевые переменные"""
        try:
            # Проверяем тип входных данных
            if not isinstance(data, pd.DataFrame):
                raise ValueError(f"Ожидался pandas.DataFrame, получен {type(data)}")
            # Проверяем наличие всех необходимых столбцов
            missing_features = [f for f in self.features if f not in data.columns]
            if missing_features:
                raise ValueError(f"Отсутствуют необходимые столбцы: {missing_features}")
            if self.target_success not in data.columns:
                raise ValueError(f"Отсутствует столбец {self.target_success}")
            if self.target_price not in data.columns:
                raise ValueError(f"Отсутствует столбец {self.target_price}")
            # Проверяем кэш
            data_hash = hash(data.to_string())
            if data_hash in self.scaler_cache:
                logger_main.info("Используем кэшированные нормализованные данные")
                return self.scaler_cache[data_hash]
            X = data[self.features].values
            X = self.scaler.fit_transform(X)
            y_success = data[self.target_success].values
            y_price = data[self.target_price].values
            # Сохраняем в кэш
            self.scaler_cache[data_hash] = (X, y_success, y_price)
            return X, y_success, y_price
        except Exception as e:
            logger_main.error(f"Ошибка при извлечении признаков: {str(e)}")
            log_exception(f"Ошибка при извлечении: {str(e)}", e)
            return np.array([]), np.array([]), np.array([])

    def prepare_lstm_data(self, X, y):
        """Подготавливает данные для LSTM"""
        try:
            sequence_length = 10
            X_lstm = []
            y_lstm = []
            for i in range(len(X) - sequence_length):
                X_lstm.append(X[i:i + sequence_length])
                y_lstm.append(y[i + sequence_length])
            return np.array(X_lstm), np.array(y_lstm)
        except Exception as e:
            logger_main.error(f"Ошибка при подготовке данных для LSTM: {str(e)}")
            log_exception(f"Ошибка при подготовке данных: {str(e)}", e)
            return np.array([]), np.array([])

__all__ = ['MLFeatureEngineer']
