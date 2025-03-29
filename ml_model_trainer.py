import numpy as np  # Добавляем импорт numpy
import os
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from utils import logger_main, log_exception

class MLModelTrainer:
    def __init__(self):
        self.rf_model = None
        self.gb_model = None
        self.lstm_model = None
        self.rf_model_path = "/root/trading_bot/models/rf_model.joblib"
        self.gb_model_path = "/root/trading_bot/models/gb_model.joblib"
        self.lstm_model_path = "/root/trading_bot/models/lstm_model.h5"
        # Создаём директорию для моделей, если она не существует
        os.makedirs(os.path.dirname(self.rf_model_path), exist_ok=True)
        # Пробуем загрузить модели
        self.load_models()
        logger_main.info("Инициализация MLModelTrainer")

    def load_models(self):
        """Загружает сохранённые модели"""
        try:
            if os.path.exists(self.rf_model_path):
                self.rf_model = joblib.load(self.rf_model_path)
                logger_main.info("Random Forest модель загружена")
            if os.path.exists(self.gb_model_path):
                self.gb_model = joblib.load(self.gb_model_path)
                logger_main.info("Gradient Boosting модель загружена")
            if os.path.exists(self.lstm_model_path):
                self.lstm_model = load_model(self.lstm_model_path)
                logger_main.info("LSTM модель загружена")
        except Exception as e:
            logger_main.error(f"Ошибка при загрузке моделей: {str(e)}")
            log_exception(f"Ошибка при загрузке моделей: {str(e)}", e)

    def save_models(self):
        """Сохраняет обученные модели"""
        try:
            if self.rf_model:
                joblib.dump(self.rf_model, self.rf_model_path)
                logger_main.info("Random Forest модель сохранена")
            if self.gb_model:
                joblib.dump(self.gb_model, self.gb_model_path)
                logger_main.info("Gradient Boosting модель сохранена")
            if self.lstm_model:
                self.lstm_model.save(self.lstm_model_path)
                logger_main.info("LSTM модель сохранена")
        except Exception as e:
            logger_main.error(f"Ошибка при сохранении моделей: {str(e)}")
            log_exception(f"Ошибка при сохранении моделей: {str(e)}", e)

    def train_models(self, X, y_success, y_price):
        """Обучает ML-модели"""
        try:
            # Разделение на тренировочные и тестовые наборы
            X_train, X_test, y_success_train, y_success_test = train_test_split(
                X, y_success, test_size=0.2, random_state=42
            )
            _, _, y_price_train, y_price_test = train_test_split(
                X, y_price, test_size=0.2, random_state=42
            )
            # Обучение Random Forest для предсказания успешности
            self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.rf_model.fit(X_train, y_success_train)
            logger_main.debug(f"Random Forest обучен, точность на тесте: {self.rf_model.score(X_test, y_success_test):.2f}")
            # Обучение Gradient Boosting для предсказания успешности
            self.gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            self.gb_model.fit(X_train, y_success_train)
            logger_main.debug(f"Gradient Boosting обучен, точность на тесте: {self.gb_model.score(X_test, y_success_test):.2f}")
            # Подготовка данных для LSTM
            feature_engineer = MLFeatureEngineer()
            X_lstm, y_lstm = feature_engineer.prepare_lstm_data(X, y_price)
            if len(X_lstm) == 0:
                logger_main.warning("Недостаточно данных для обучения LSTM")
                return
            X_lstm_train, X_lstm_test, y_lstm_train, y_lstm_test = train_test_split(
                X_lstm, y_lstm, test_size=0.2, random_state=42
            )
            # Обучение LSTM для предсказания цен (с использованием GPU)
            self.lstm_model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(X_lstm.shape[1], X_lstm.shape[2])),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(1)
            ])
            self.lstm_model.compile(optimizer='adam', loss='mse')
            self.lstm_model.fit(X_lstm_train, y_lstm_train, epochs=10, batch_size=64, verbose=0)  # Увеличиваем batch_size для GPU
            logger_main.debug("LSTM обучен")
            # Сохраняем модели после обучения
            self.save_models()
        except Exception as e:
            logger_main.error(f"Ошибка при обучении моделей: {str(e)}")
            log_exception(f"Ошибка при обучении моделей: {str(e)}", e)

    def predict_success(self, data):
        """Предсказывает успешность стратегии (синхронный метод)"""
        if self.rf_model is None or self.gb_model is None:
            logger_main.warning("Модели не обучены, пропускаем предсказание успешности")
            return None
        try:
            feature_engineer = MLFeatureEngineer()
            X, _, _ = feature_engineer.extract_features(data)
            # Предсказания от обеих моделей
            rf_proba = self.rf_model.predict_proba(X)
            gb_proba = self.gb_model.predict_proba(X)
            # Обрабатываем случай, когда модель обучена на одном классе
            rf_pred = rf_proba[:, 1] if rf_proba.shape[1] > 1 else rf_proba[:, 0] if self.rf_model.classes_[0] == 1 else 1 - rf_proba[:, 0]
            gb_pred = gb_proba[:, 1] if gb_proba.shape[1] > 1 else gb_proba[:, 0] if self.gb_model.classes_[0] == 1 else 1 - gb_proba[:, 0]
            # Комбинируем предсказания (усреднение)
            combined_pred = (rf_pred + gb_pred) / 2
            logger_main.debug(f"Предсказанная вероятность успешности: {combined_pred}")
            return combined_pred
        except Exception as e:
            logger_main.error(f"Ошибка при предсказании успешности: {str(e)}")
            log_exception(f"Ошибка при предсказании: {str(e)}", e)
            return None

    def predict_price(self, data):
        """Предсказывает будущую цену"""
        if self.lstm_model is None:
            logger_main.warning("LSTM модель не обучена, пропускаем предсказание цены")
            return None
        try:
            feature_engineer = MLFeatureEngineer()
            X, _, _ = feature_engineer.extract_features(data)
            X_lstm, _ = feature_engineer.prepare_lstm_data(X, np.zeros(len(X)))
            pred = self.lstm_model.predict(X_lstm, verbose=0)
            logger_main.debug(f"Предсказанная цена: {pred.flatten()}")
            return pred.flatten()
        except Exception as e:
            logger_main.error(f"Ошибка при предсказании цены: {str(e)}")
            log_exception(f"Ошибка при предсказании: {str(e)}", e)
            return None

__all__ = ['MLModelTrainer']
