import tensorflow as tf
import pandas as pd
import numpy as np
import asyncio
from utils import logger_main, log_exception

# Ограничение использования памяти GPU
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
            tf.config.experimental.set_virtual_device_configuration(gpu, [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=10240)])  # Ограничение 10 ГБ
        logger_main.info("Установлено динамическое выделение памяти GPU с лимитом 10 ГБ")
    except RuntimeError as e:
        logger_main.error(f"Ошибка при настройке GPU: {str(e)}")

def prepare_data(ohlcv):
    try:
        df = ohlcv.reset_index()
        if not all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']):
            logger_main.error(f"Недостаточно данных в ohlcv: {df.columns}")
            return None
        data = df[['open', 'high', 'low', 'close', 'volume']].values
        logger_main.debug(f"Подготовленные данные: форма {data.shape}, пример: {data[:2]}")
        return data
    except Exception as e:
        logger_main.error(f"Ошибка в prepare_data: {str(e)}")
        return None

async def train_and_predict(ohlcv):
    try:
        logger_main.debug("Начало train_and_predict для символа с индексом: {ohlcv.index[-1]}")
        data = prepare_data(ohlcv)
        if data is None or len(data) < 20:
            logger_main.warning(f"Недостаточно данных для модели: {len(data) if data is not None else 'None'}")
            return None
        # Уменьшенная модель
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(20, return_sequences=False, input_shape=(20, 5)),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='mse')
        logger_main.debug("Модель инициализирована и скомпилирована")
        # Подготовка данных
        X = np.array([data[i-20:i] for i in range(20, len(data))])
        y = data[20:, 3]  # Используем 'close' для предсказания
        X = np.reshape(X, (X.shape[0], X.shape[1], 5))
        logger_main.debug(f"Данные для обучения: X форма {X.shape}, y форма {y.shape}")
        # Обучение с таймаутом
        loop = asyncio.get_event_loop()
        model_fit = loop.run_in_executor(None, lambda: model.fit(X, y, epochs=1, batch_size=16, verbose=0))
        try:
            await asyncio.wait_for(model_fit, timeout=30)
            logger_main.debug("Обучение модели завершено успешно")
        except asyncio.TimeoutError:
            logger_main.warning("Таймаут обучения модели")
            tf.keras.backend.clear_session()
            return None
        # Предсказание
        last_sequence = np.array([data[-20:]])
        last_sequence = np.reshape(last_sequence, (1, last_sequence.shape[1], 5))
        logger_main.debug(f"Последовательность для предсказания: форма {last_sequence.shape}")
        prediction = model.predict(last_sequence, verbose=0)
        signal = 1 if prediction[0][0] > 0.5 else -1
        logger_main.info(f"Модель предсказала сигнал: {signal} для {ohlcv.index[-1]}")
        # Очистка памяти
        tf.keras.backend.clear_session()
        del model
        import gc
        gc.collect()
        return {'signal': pd.Series([signal])}
    except Exception as e:
        log_exception(f"Ошибка в модели для предсказания: {str(e)}", e)
        return None

__all__ = ['train_and_predict']
