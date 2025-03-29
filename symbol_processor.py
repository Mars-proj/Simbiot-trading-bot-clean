import asyncio
from utils import logger_main, log_exception
from symbol_data_fetcher import fetch_ohlcv_for_symbol
from symbol_handler import process_symbol
from trade_pool import global_trade_pool

async def process_user_symbols(exchange, trade_executor, user_id, ex_name, market_conditions, symbols, groups, loop=None):
    logger_main.info(f"Начало обработки символов для {user_id} на {ex_name}")
    logger_main.debug(f"Получено символов: {len(symbols)}, групп: {len(groups)}")
    try:
        # Устанавливаем цикл событий, если он передан
        if loop is None:
            loop = asyncio.get_running_loop()
        logger_main.debug(f"Используем цикл событий: {loop}")

        # Получаем баланс пользователя перед обработкой символов
        logger_main.debug(f"Запрашиваем баланс для {user_id} на {ex_name}")
        balance = await trade_executor.fetch_balance_with_cache(exchange, user_id, force_refresh=True)
        if balance is None:
            logger_main.error(f"Не удалось получить баланс для {user_id} на {ex_name}")
        else:
            logger_main.debug(f"Получен баланс для {user_id}: {balance}")
            usdt_balance = balance.get('USDT', {})
            logger_main.info(f"Баланс {user_id} на {ex_name}: свободно={usdt_balance.get('free', 0)}, заблокировано={usdt_balance.get('used', 0)}, итого={usdt_balance.get('total', 0)} USDT")

        # Проверяем список символов перед созданием задач
        logger_main.debug(f"Символы для обработки: {symbols}")
        if not symbols:
            logger_main.warning(f"Список символов пуст для {user_id} на {ex_name}, пропускаем обработку")
            return []

        # Создаём задачи для получения OHLCV-данных
        logger_main.debug("Создаём список задач для получения OHLCV")
        tasks = [fetch_ohlcv_for_symbol(exchange, symbol) for symbol in symbols]
        logger_main.debug(f"Создано {len(tasks)} задач для получения OHLCV")

        # Выполняем задачи
        logger_main.debug("Запускаем задачи для получения OHLCV")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger_main.debug(f"Результаты получения OHLCV: {results}")

        # Анализируем результаты
        successful_symbols = sum(1 for _, ohlcv in results if ohlcv is not None)
        logger_main.info(f"Успешно загружены OHLCV-данные для {successful_symbols} из {len(symbols)} символов")

        # Создаём задачи для обработки символов
        tasks = []
        for symbol, ohlcv in results:
            if ohlcv is None:
                logger_main.warning(f"OHLCV для {symbol} не загружен (None)")
                continue
            # Добавляем отладочный лог для сырых данных
            logger_main.debug(f"Сырые OHLCV-данные для {symbol}: {ohlcv.to_dict()}")
            logger_main.info(f"Обрабатываем символ {symbol} для пользователя {user_id} на {ex_name}")

            # Определяем группу символа
            symbol_group = None
            for group_name, group_symbols in groups.items():
                if symbol in group_symbols:
                    symbol_group = group_name
                    break
            logger_main.debug(f"Символ {symbol} принадлежит группе: {symbol_group}")

            # Передаём trade_executor, группу и market_conditions в process_symbol
            tasks.append(process_symbol(exchange, trade_executor, symbol, ohlcv, user_id, symbol_group, market_conditions))

        logger_main.debug("Создаём список задач для обработки символов")
        logger_main.info(f"Создано {len(tasks)} задач для обработки символов")

        # Выполняем задачи обработки символов
        logger_main.debug("Запускаем обработку символов")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger_main.debug("Обработка символов завершена")

        # Получаем все сделки
        logger_main.debug("Начало получения всех сделок из TradePool")
        trades = await global_trade_pool.get_all_trades()
        logger_main.debug(f"Получено {len(trades)} сделок для анализа")
        return trades

    except Exception as e:
        logger_main.error(f"Ошибка при обработке символов для {user_id} на {ex_name}: {str(e)}")
        log_exception(f"Ошибка при обработке символов: {str(e)}", e)
        raise

__all__ = ['process_user_symbols']
