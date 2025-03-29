import asyncio
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from logging_setup import logger_main, logger_exceptions
from global_objects import global_trade_pool
from backtest_cycle import run_backtest  # Для получения бэктестов
import random

# Интервал переобучения (24 часа)
RETRAINING_INTERVAL = 24 * 60 * 60  # Можно сделать динамическим через конфигурацию

class RetrainingManager:
    def __init__(self):
        self.sequence_length = 10  # Длина последовательности для LSTM (инициализируем первым)
        self.scaler = MinMaxScaler()
        self.model = self._build_model()  # Теперь вызываем после определения sequence_length
        logger_main.info("Initialized RetrainingManager")

    def _build_model(self):
        """Создаёт модель LSTM для генерации сигналов"""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(self.sequence_length, 5)),  # 5 признаков: price, amount, signal, strategy_signal, pnl
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(3, activation='softmax')  # 3 класса: Buy (1), Sell (-1), Neutral (0)
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    def _prepare_data(self, trades):
        """Подготавливает данные для обучения"""
        if not trades:
            return None, None
        # Преобразуем сделки в DataFrame
        df = pd.DataFrame([trade['trade'] for trade in trades])
        if 'price' not in df or 'amount' not in df:
            logger_main.warning("Missing required fields in trade data")
            return None, None
        # Добавляем сигналы и стратегии
        df['signal'] = [trade['signal'] for trade in trades]
        df['strategy_signal'] = [sum(trade['strategies'].values()) for trade in trades]
        df['pnl'] = df.get('pnl', 0.0)
        # Заполняем пропуски
        df = df.fillna(0)
        # Выбираем признаки
        features = df[['price', 'amount', 'signal', 'strategy_signal', 'pnl']].values
        # Нормализуем данные
        features_scaled = self.scaler.fit_transform(features)
        # Создаём последовательности
        X, y = [], []
        for i in range(len(features_scaled) - self.sequence_length):
            X.append(features_scaled[i:i + self.sequence_length])
            # Определяем целевой сигнал (Buy=1, Sell=2, Neutral=0)
            next_signal = df['signal'].iloc[i + self.sequence_length]
            if next_signal > 0:
                y.append(1)  # Buy
            elif next_signal < 0:
                y.append(2)  # Sell
            else:
                y.append(0)  # Neutral
        if not X or not y:
            return None, None
        return np.array(X), np.array(y)

    async def retrain_system(self):
        """Переобучает систему на основе 50% бэктестов и 50% реальных торгов"""
        while True:
            try:
                logger_main.info("Starting system retraining")
                # Получаем реальные сделки из общего пула
                real_trades = await global_trade_pool.get_all_trades()
                if not real_trades:
                    logger_main.warning("No real trades available for retraining")
                    await asyncio.sleep(RETRAINING_INTERVAL)
                    continue
                # Получаем бэктесты
                backtest_trades = await run_backtest()  # Реальная функция бэктеста
                if not backtest_trades:
                    logger_main.warning("No backtest trades available for retraining")
                    backtest_trades = []
                # Комбинируем данные: 50% реальных сделок, 50% бэктестов
                total_real = len(real_trades)
                total_backtest = len(backtest_trades)
                target_count = min(total_real, total_backtest)
                if target_count == 0:
                    logger_main.warning("Not enough trades for retraining")
                    await asyncio.sleep(RETRAINING_INTERVAL)
                    continue
                # Выбираем 50% от каждого набора
                real_sample = random.sample(real_trades, target_count // 2) if total_real >= target_count // 2 else real_trades
                backtest_sample = random.sample(backtest_trades, target_count // 2) if total_backtest >= target_count // 2 else backtest_trades
                combined_trades = real_sample + backtest_sample
                logger_main.info(f"Combined {len(real_sample)} real trades and {len(backtest_sample)} backtest trades for retraining")
                # Подготавливаем данные для обучения
                X, y = self._prepare_data(combined_trades)
                if X is None or y is None:
                    logger_main.warning("Failed to prepare data for retraining")
                    await asyncio.sleep(RETRAINING_INTERVAL)
                    continue
                # Обучаем модель асинхронно, используя asyncio.to_thread
                await asyncio.to_thread(self.model.fit, X, y, epochs=5, batch_size=32, verbose=0)
                logger_main.info("Model retraining completed")
                # Ждём 24 часа до следующего переобучения
                await asyncio.sleep(RETRAINING_INTERVAL)
            except Exception as e:
                logger_main.error(f"Error during system retraining: {str(e)}")
                logger_exceptions.error(f"Error during retraining: {str(e)}", exc_info=True)
                await asyncio.sleep(RETRAINING_INTERVAL)  # Продолжаем после ошибки

    async def generate_signal(self, recent_data):
        """Генерирует сигнал на основе последних данных"""
        try:
            X, _ = self._prepare_data(recent_data)
            if X is None:
                logger_main.warning("Failed to prepare data for signal generation")
                return 0  # Neutral
            # Предсказываем асинхронно, используя asyncio.to_thread
            prediction = await asyncio.to_thread(self.model.predict, X[-1:], verbose=0)
            signal_class = np.argmax(prediction, axis=1)[0]
            if signal_class == 1:
                return 1  # Buy
            elif signal_class == 2:
                return -1  # Sell
            else:
                return 0  # Neutral
        except Exception as e:
            logger_main.error(f"Error generating signal: {str(e)}")
            logger_exceptions.error(f"Error generating signal: {str(e)}", exc_info=True)
            return 0  # Neutral

# Инициализация менеджера переобучения
retraining_manager = RetrainingManager()

# Запуск задачи переобучения
def start_retraining():
    """Запускает задачу переобучения в фоновом режиме"""
    asyncio.create_task(retraining_manager.retrain_system())

__all__ = ['retraining_manager', 'start_retraining']
