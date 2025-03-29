import tensorflow as tf
import os
from logging_setup import logger_main
from utils import log_exception
from global_objects import global_trade_pool
from retraining_data_preprocessor import RetrainDataPreprocessor

class RetrainEngine:
    def __init__(self):
        self.model_path = "/root/trading_bot/trade_model.h5"
        self.data_preprocessor = RetrainDataPreprocessor()
        self.model = self.build_model()
        self.model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                          loss='binary_crossentropy',
                          metrics=['accuracy'])
        self.load_model()

    def initialize_logging(self):
        """Initializes logging for RetrainEngine and its dependencies"""
        logger_main.info("RetrainEngine initialized, model created")
        self.data_preprocessor.initialize_logging()
        # Log model loading status
        if os.path.exists(self.model_path):
            logger_main.info("Model loaded from file")
        else:
            logger_main.info("Model file not found, using new model")

    def build_model(self):
        """Builds the model with regularization and dropout"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(self.data_preprocessor.input_size,),
                                 kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu',
                                 kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu',
                                 kernel_regularizer=tf.keras.regularizers.l2(0.01)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        return model

    def load_model(self):
        """Loads the model if it exists"""
        try:
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
            # Logging moved to initialize_logging
        except Exception as e:
            log_exception("Error loading model", e)

    def save_model(self):
        """Saves the model"""
        try:
            self.model.save(self.model_path)
            logger_main.info("Model saved to file")
        except Exception as e:
            log_exception("Error saving model", e)

    def predict(self, signal_data):
        """Predicts the success probability of a trade"""
        try:
            features = self.data_preprocessor.preprocess_data(signal_data)
            if features is None:
                logger_main.warning("Failed to preprocess data for prediction, returning 0.5")
                return 0.5
            features = features.reshape(1, -1)
            features_tensor = tf.convert_to_tensor(features, dtype=tf.float32)
            with tf.device('/GPU:0'):
                probability = self.model.predict(features_tensor, verbose=0)[0][0]
            logger_main.debug(f"Predicted success probability for {signal_data.get('symbol', 'unknown')}: {probability}")
            return float(probability)
        except Exception as e:
            log_exception("Error during prediction", e)
            return 0.5

    async def retrain(self, trades=None):
        pass  # Placeholder for retrain method, to be implemented later
