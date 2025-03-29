import asyncio
import pandas as pd
from utils import logger_main, log_exception
from trade_pool import global_trade_pool
from trade_execution import execute_trade

async def monitor_position(exchange, trade_data, order, trade_executor):
    """
    Мониторит позицию с динамическими Stop-Loss, Take-Profit и частичным закрытием.
    Аргументы:
    - exchange: Объект биржи (ccxt).
    - trade_data: Словарь с данными сделки.
    - order: Результат выполнения ордера.
    - trade_executor: Экземпляр TradeExecutor для доступа к его атрибутам и методам.
    """
    symbol = trade_data['symbol']
    side = trade_data['side']
    amount = trade_data['amount']
    entry_price = trade_data['price']
    user_id = trade_data['user_id']
    market_conditions = trade_data.get('market_conditions', {})
    trade_id = trade_data.get('trade_id', order.get('id', 'unknown'))
    # Вычисляем динамические точки выхода
    stop_loss_price, take_profit_drop = trade_executor.calculate_dynamic_exit_points(market_conditions, symbol, entry_price)
    # Инициализируем пик для динамического Take-Profit
    peak_price = entry_price
    while True:
        try:
            # Получаем текущую цену
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            logger_main.debug(f"Мониторинг {symbol}: текущая цена = {current_price}")
            # Проверяем Stop-Loss
            if side == "buy" and current_price <= stop_loss_price:
                logger_main.info(f"Stop-Loss сработал для {symbol}: цена {current_price} <= {stop_loss_price}")
                close_trade = {
                    'user_id': user_id,
                    'exchange_id': exchange.id,
                    'symbol': symbol,
                    'side': 'sell',
                    'price': current_price,
                    'amount': amount,
                    'timestamp': pd.Timestamp.now(),
                    'market_conditions': market_conditions,
                    'symbol_group': trade_data['symbol_group'],
                    'strategy': trade_data['strategy']
                }
                close_order = await execute_trade(exchange, close_trade, trade_executor)
                if close_order:
                    # Рассчитываем PNL
                    pnl = (current_price - entry_price) * amount
                    trade_executor.trade_stats['total_pnl'] += pnl
                    if pnl > 0:
                        trade_executor.trade_stats['successful_trades'] += 1
                    logger_main.info(f"PNL от Stop-Loss для {symbol}: {pnl:.2f} USDT, общий PNL: {trade_executor.trade_stats['total_pnl']:.2f}")
                    # Обновляем PNL в trade_pool
                    await global_trade_pool.update_trade_pnl(trade_id, pnl, status="completed")
                break
            # Обновляем пик для Take-Profit
            if side == "buy" and current_price > peak_price:
                peak_price = current_price
                logger_main.debug(f"Новый пик для {symbol}: {peak_price}")
            # Проверяем динамический Take-Profit
            if side == "buy" and peak_price > entry_price:
                drop_from_peak = (peak_price - current_price) / peak_price
                if drop_from_peak >= take_profit_drop:
                    logger_main.info(f"Take-Profit сработал для {symbol}: падение от пика {drop_from_peak:.2%} >= {take_profit_drop:.2%}")
                    close_trade = {
                        'user_id': user_id,
                        'exchange_id': exchange.id,
                        'symbol': symbol,
                        'side': 'sell',
                        'price': current_price,
                        'amount': amount,
                        'timestamp': pd.Timestamp.now(),
                        'market_conditions': market_conditions,
                        'symbol_group': trade_data['symbol_group'],
                        'strategy': trade_data['strategy']
                    }
                    close_order = await execute_trade(exchange, close_trade, trade_executor)
                    if close_order:
                        # Рассчитываем PNL
                        pnl = (current_price - entry_price) * amount
                        trade_executor.trade_stats['total_pnl'] += pnl
                        if pnl > 0:
                            trade_executor.trade_stats['successful_trades'] += 1
                        logger_main.info(f"PNL от Take-Profit для {symbol}: {pnl:.2f} USDT, общий PNL: {trade_executor.trade_stats['total_pnl']:.2f}")
                        # Обновляем PNL в trade_pool
                        await global_trade_pool.update_trade_pnl(trade_id, pnl, status="completed")
                    break
            # Проверяем частичное закрытие
            if side == "buy":
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                close_amount = trade_executor.calculate_partial_close_amount(amount, profit_pct)
                if close_amount > 0:
                    logger_main.info(f"Частичное закрытие для {symbol}: закрываем {close_amount} из {amount}")
                    close_trade = {
                        'user_id': user_id,
                        'exchange_id': exchange.id,
                        'symbol': symbol,
                        'side': 'sell',
                        'price': current_price,
                        'amount': close_amount,
                        'timestamp': pd.Timestamp.now(),
                        'market_conditions': market_conditions,
                        'symbol_group': trade_data['symbol_group'],
                        'strategy': trade_data['strategy']
                    }
                    close_order = await execute_trade(exchange, close_trade, trade_executor)
                    if close_order:
                        # Рассчитываем PNL для частичного закрытия
                        pnl = (current_price - entry_price) * close_amount
                        trade_executor.trade_stats['total_pnl'] += pnl
                        if pnl > 0:
                            trade_executor.trade_stats['successful_trades'] += 1
                        logger_main.info(f"PNL от частичного закрытия для {symbol}: {pnl:.2f} USDT, общий PNL: {trade_executor.trade_stats['total_pnl']:.2f}")
                        # Обновляем PNL в trade_pool
                        await global_trade_pool.update_trade_pnl(trade_id, pnl, status="partially_closed")
                        amount -= close_amount
                        if amount <= 0:
                            break
            await asyncio.sleep(60)  # Проверяем каждые 60 секунд
        except Exception as e:
            logger_main.error(f"Ошибка при мониторинге позиции {symbol}: {str(e)}")
            log_exception(f"Ошибка при мониторинге: {str(e)}", e)
            break

__all__ = ['monitor_position']
