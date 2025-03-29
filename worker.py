import asyncio
import time
from utils import logger_main, performance_monitor
from data_fetcher import fetch_ohlcv
from signal_generator import generate_signals

async def worker_func(queue, exchanges, trade_executors, train_and_predict):
    """
    Функция воркера для обработки задач из очереди.
    :param queue: Очередь задач (user_id, ex_name, symbol).
    :param exchanges: Словарь обменников {user_id: {ex_name: exchange}}.
    :param trade_executors: Словарь экземпляров TradeExecutor {user_id: {ex_name: trade_executor}}.
    :param train_and_predict: Функция для обучения и предсказания ML-модели.
    """
    while True:
        try:
            user_id, ex_name, symbol = await queue.get()
            if symbol is None:
                queue.task_done()
                continue
            start_time = time.time()
            logger_main.info(f"Обрабатываем символ {symbol} для пользователя {user_id} на {ex_name} (время: {start_time})")
            performance_monitor.start_task(f"{user_id}:{ex_name}:{symbol}")
            
            # Получение OHLCV данных
            ohlcv = await fetch_ohlcv(exchanges[user_id][ex_name], symbol)
            if isinstance(ohlcv, str):
                logger_main.warning(f"Ошибка при получении OHLCV для {symbol}: {ohlcv}")
                queue.task_done()
                continue
            
            # Генерация комбинированного сигнала
            signal = generate_signals(ohlcv)
            logger_main.info(f"Комбинированный сигнал для {symbol}: {signal} (время: {time.time()})")
            
            # Запуск ML-модели
            logger_main.info(f"Запуск ML-модели для {symbol} (время: {time.time()})")
            ml_signal = await train_and_predict(ohlcv)
            logger_main.debug(f"ML-результат для {symbol}: {ml_signal}")
            logger_main.info(f"ML сигнал для {symbol} на {ex_name}: {ml_signal['signal'].iloc[0]} (время: {time.time()})")
            
            # Проверка расхождения сигналов
            if ml_signal['signal'].iloc[0] != signal:
                logger_main.info(f"Уведомление: ML сигнал ({ml_signal['signal'].iloc[0]}) отличается от комбинированного ({signal}) для {symbol}")
            
            # Используем ML-сигнал как окончательный
            final_signal = ml_signal['signal'].iloc[0]
            performance_monitor.record_signal(final_signal)
            
            # Выполнение торговой операции
            logger_main.debug(f"Перед торговлей для {symbol}, сигнал: {final_signal}, память: {performance_monitor.get_memory_usage()}% RAM (время: {time.time()})")
            trade_executor = trade_executors[user_id][ex_name]
            trade_result = await trade_executor.execute_trade(exchanges[user_id][ex_name], symbol, final_signal)
            if trade_result:
                logger_main.info(f"Торговля выполнена для {symbol}: {trade_result}")
            
            # Завершение задачи
            performance_monitor.end_task(f"{user_id}:{ex_name}:{symbol}")
            logger_main.info(f"Ресурсы: RAM {performance_monitor.get_memory_usage()}%, CPU {performance_monitor.get_cpu_usage()}% (время: {time.time()})")
            logger_main.info(f"Статистика сигналов: {performance_monitor.get_signal_stats()} (время: {time.time()})")
            
        except Exception as e:
            logger_main.error(f"Ошибка в воркере для {symbol}: {str(e)}")
            log_exception(f"Ошибка в воркере для {symbol}", e)
        finally:
            queue.task_done()

__all__ = ['worker_func']
