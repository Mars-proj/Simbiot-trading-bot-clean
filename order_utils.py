from utils import logger_main, log_exception

async def check_can_buy(trade_executor, balance, min_trade_amount_usdt=5.015):
    """Проверка, достаточно ли баланса для покупки"""
    if 'USDT' not in balance or 'free' not in balance['USDT']:
        logger_main.error("Не удалось получить свободный баланс USDT")
        trade_executor.can_buy = False
        return False
    usdt_balance = float(balance['USDT']['free'])
    required_balance = min_trade_amount_usdt * 1.1  # Запас 10%
    if usdt_balance < required_balance:
        logger_main.warning(f"Недостаточно средств для покупки: доступно {usdt_balance} USDT, требуется минимум {required_balance} USDT")
        trade_executor.can_buy = False
    else:
        logger_main.debug(f"Достаточно средств для покупки: доступно {usdt_balance} USDT")
        trade_executor.can_buy = True
    return trade_executor.can_buy

async def update_order_status(exchange, order, trade_data):
    """Проверка статуса ордера и обновление trade_data в пуле"""
    try:
        # Получаем статус ордера через API биржи
        order_status = await exchange.fetch_order(order['id'], trade_data['symbol'])
        logger_main.debug(f"Статус ордера для {trade_data['symbol']}: {order_status['status']}")

        # Обновляем статус в trade_data
        if order_status['status'] == 'closed' and order_status['filled'] == order_status['amount']:
            trade_data['status'] = 'successful'
            logger_main.info(f"Ордер для {trade_data['symbol']} полностью выполнен, статус обновлён на 'successful'")
        elif order_status['status'] in ['canceled', 'expired', 'rejected']:
            trade_data['status'] = 'failed'
            logger_main.info(f"Ордер для {trade_data['symbol']} отменён или не выполнен, статус обновлён на 'failed'")
        else:
            logger_main.debug(f"Ордер для {trade_data['symbol']} всё ещё в обработке, статус остаётся 'pending'")
            return  # Оставляем статус pending, если ордер ещё не завершён

        # Обновляем trade_data в пуле
        from trade_pool import global_trade_pool
        await global_trade_pool.update_trade(trade_data)
        logger_main.debug(f"Статус сделки для {trade_data['symbol']} обновлён в пуле: {trade_data['status']}")

    except Exception as e:
        logger_main.error(f"Ошибка при проверке статуса ордера для {trade_data['symbol']}: {str(e)}")
        log_exception(f"Ошибка при проверке статуса ордера для {trade_data['symbol']}", e)

__all__ = ['check_can_buy', 'update_order_status']
