import asyncio
import ccxt.async_support as ccxt
from trade_executor_core import TradeExecutor
from trade_executor_signals import execute_trade as execute_trade_signal
from logging_setup import logger_main, logger_exceptions
from signal_generator_core import generate_signals
from strategies import MovingAverageStrategy, RSIDivergenceStrategy, BollingerBandsBreakoutStrategy, MACDTrendFollowingStrategy
from trade_pool_queries import get_all_trades as get_trade_pool
from global_objects import global_trade_pool
from symbol_filter import filter_symbols
from config_keys import API_KEYS, PREFERRED_EXCHANGES
from bot_user_data import user_data, get_user_deposit, get_user_assets, add_user_trade
from redis_client import get_trades_from_cache, add_trade_to_cache, add_to_problematic_symbols  # Импортируем функции напрямую
from retraining_manager import retraining_manager
from backtest_cycle import run_backtest as run_backtest_cycle

# Хранилище ошибок для каждого пользователя
trade_errors = {}

async def start_trading(user_id):
    """Запускает торговлю для пользователя"""
    if user_id is None or user_id not in API_KEYS:
        logger_main.warning(f"Cannot start trading: user {user_id} not registered")
        return
    try:
        logger_main.debug(f"Starting trading for user {user_id}")
        # Используем предпочитаемую биржу пользователя
        exchange_name = PREFERRED_EXCHANGES[user_id]
        exchange_config = API_KEYS[user_id][exchange_name]
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': exchange_config['api_key'],
            'secret': exchange_config['api_secret'],
            'enableRateLimit': True,
        })
        trade_executor = TradeExecutor()
        await trade_executor.initialize_deposit(exchange, user_id)
        # Проверяем депозит перед началом торговли
        if trade_executor.risk_calculator.total_deposit_usdt <= 0:
            logger_main.warning(f"Cannot start trading for user {user_id}: deposit is 0.0 USDT. Switching to backtest mode.")
            await run_backtest(exchange, trade_executor, user_id, exchange_name)
        else:
            await process_user_symbols(exchange, trade_executor, user_id, exchange_name)
        await exchange.close()
        logger_main.info(f"Trading completed for user {user_id}")
    except Exception as e:
        logger_main.error(f"Error starting trading for {user_id}: {str(e)}")
        logger_exceptions.error(f"Error starting trading: {str(e)}", exc_info=True)
        if user_id not in trade_errors:
            trade_errors[user_id] = []
        trade_errors[user_id].append(f"Error starting trading: {str(e)}")

async def run_backtest(exchange, trade_executor, user_id, ex_name):
    """Запускает бэктест, если депозит равен 0"""
    logger_main.info(f"Starting backtest for user {user_id} on {ex_name}")
    try:
        # Фильтруем символы
        filtered_symbols = await filter_symbols(exchange)
        logger_main.info(f"Found {len(filtered_symbols)} symbols for backtest for {user_id} on {ex_name}: {filtered_symbols[:10]}...")
        # Определяем стратегии для бэктеста
        strategies = [
            'MovingAverageStrategy',
            'RSIDivergenceStrategy',
            'BollingerBandsBreakoutStrategy',
            'MACDTrendFollowingStrategy'
        ]
        # Вызываем бэктест из backtest_cycle.py
        backtest_results = await run_backtest_cycle(exchange, trade_executor, filtered_symbols, strategies)
        logger_main.info(f"Backtest completed for user {user_id} on {ex_name}. Results: {backtest_results}")
    except Exception as e:
        logger_main.error(f"Error during backtest for user {user_id} on {ex_name}: {str(e)}")
        logger_exceptions.error(f"Error during backtest: {str(e)}", exc_info=True)

async def process_user_symbols(exchange, trade_executor, user_id, ex_name):
    """Обрабатывает символы для торговли"""
    if not user_id:
        logger_main.warning("Cannot process symbols: user_id is missing")
        return
    try:
        logger_main.debug(f"Starting symbol filtering for {user_id} on {ex_name}")
        symbols = await filter_symbols(exchange)
        logger_main.info(f"Found {len(symbols)} symbols after filtering for {user_id} on {ex_name}: {symbols[:10]}...")
        strategies = [
            MovingAverageStrategy(),
            RSIDivergenceStrategy(),
            BollingerBandsBreakoutStrategy(),
            MACDTrendFollowingStrategy()
        ]
        # Получаем активы пользователя
        user_assets = get_user_assets(user_id)
        for symbol in symbols:
            try:
                logger_main.info(f"Processing symbol {symbol} for user {user_id} on {ex_name}")
                if not trade_executor.risk_calculator.check_drawdown(exchange):
                    logger_main.warning(f"Trading for {symbol} cancelled due to drawdown limit")
                    if user_id not in trade_errors:
                        trade_errors[user_id] = []
                    trade_errors[user_id].append(f"Trading for {symbol} cancelled due to drawdown limit")
                    continue
                ohlcv_data = await exchange.fetch_ohlcv(symbol, timeframe='4h', limit=100)
                if ohlcv_data is None:
                    logger_main.warning(f"Failed to fetch OHLCV for {symbol}: data missing")
                    if user_id not in trade_errors:
                        trade_errors[user_id] = []
                    trade_errors[user_id].append(f"Failed to fetch data for {symbol}: data missing")
                    # Кэшируем проблемный символ
                    await add_to_problematic_symbols(symbol, ex_name)
                    continue
                result = await generate_signals(ohlcv_data, timeframe='4h', symbol=symbol)
                if result[0] is None:  # Если генерация сигнала не удалась
                    logger_main.warning(f"Failed to generate signal for {symbol}")
                    # Кэшируем проблемный символ
                    await add_to_problematic_symbols(symbol, ex_name)
                    continue
                signal, metrics = result
                logger_main.info(f"Generated signal via signal_generator for {symbol}: {signal}, metrics: {metrics}")
                strategy_signals = {}
                for strategy in strategies:
                    strategy_name = strategy.__class__.__name__
                    strategy_signal = strategy.generate_signal(ohlcv_data)
                    strategy_signals[strategy_name] = strategy_signal
                    logger_main.debug(f"Signal from {strategy_name} for {symbol}: {strategy_signal}")
                combined_signal = sum(strategy_signals.values()) + signal
                # Получаем сигнал от retraining_manager
                recent_trades = await get_trades_from_cache(user_id)  # Используем функцию напрямую
                market_conditions = {'avg_volatility': metrics.get('volatility', 0.1)}  # Пример рыночных условий
                confidence = 0.5  # Базовая уверенность
                ml_signal = None
                if recent_trades and len(recent_trades) >= 10:  # Нужно минимум 10 сделок для генерации сигнала
                    ml_signal = await retraining_manager.generate_signal(recent_trades[-10:])
                    logger_main.info(f"Generated ML signal for {symbol}: {ml_signal}")
                    combined_signal += ml_signal
                    confidence = 0.8 if abs(ml_signal) > 0 else 0.5  # Увеличиваем уверенность, если ML сигнал сильный
                if combined_signal > 0:
                    final_signal = 1  # Buy
                elif combined_signal < 0:
                    final_signal = -1  # Sell
                else:
                    final_signal = 0  # Neutral
                logger_main.info(f"Combined signal for {symbol}: {final_signal} (signal_generator: {signal}, strategies: {strategy_signals}, ML: {ml_signal if ml_signal is not None else 'N/A'})")
                if final_signal != 0:
                    try:
                        side = 'buy' if final_signal == 1 else 'sell'
                        # Вызываем execute_trade_signal без await, чтобы проверить результат
                        order_coroutine = execute_trade_signal(exchange, symbol, side, user_id, trade_executor, confidence=confidence, market_conditions=market_conditions)
                        logger_main.debug(f"execute_trade_signal returned: {order_coroutine}")
                        if order_coroutine is None or isinstance(order_coroutine, bool):
                            logger_main.warning(f"Trade execution failed for {symbol}: execute_trade_signal returned {order_coroutine}")
                            if user_id not in trade_errors:
                                trade_errors[user_id] = []
                            trade_errors[user_id].append(f"Trade execution failed for {symbol}: execute_trade_signal returned {order_coroutine}")
                            # Кэшируем проблемный символ
                            await add_to_problematic_symbols(symbol, ex_name)
                            continue
                        # Теперь безопасно используем await
                        order = await order_coroutine
                        if order is None:
                            logger_main.warning(f"Trade execution failed for {symbol}: order is None after await")
                            if user_id not in trade_errors:
                                trade_errors[user_id] = []
                            trade_errors[user_id].append(f"Trade execution failed for {symbol}: order is None after await")
                            # Кэшируем проблемный символ
                            await add_to_problematic_symbols(symbol, ex_name)
                            continue
                        logger_main.info(f"Trade executed for {symbol}: {order}")
                        trade_log = {
                            'user_id': user_id,
                            'symbol': symbol,
                            'side': order['side'],
                            'amount': order['amount'],
                            'order_type': order['type'],
                            'price': order['price'],
                            'exchange': ex_name,
                            'timestamp': order['datetime'],
                            'stop_price': order.get('stopPrice', 'N/A'),
                            'pnl': 0,  # Пока не рассчитываем PNL
                            'roi': 'N/A',
                        }
                        # Сохраняем сделку в user_data
                        add_user_trade(user_id, trade_log, signal, strategy_signals)
                        # Сохраняем сделку в кэш Redis
                        trade_info = {
                            'trade': trade_log,
                            'signal': signal,
                            'strategies': strategy_signals,
                            'timestamp': int(asyncio.get_event_loop().time())
                        }
                        await add_trade_to_cache(user_id, trade_info)  # Используем функцию напрямую
                        await global_trade_pool.add_trade(trade_log)
                        # Обновляем депозит после сделки
                        await trade_executor.risk_calculator.update_deposit(exchange)
                        logger_main.info(f"Deposit updated for user {user_id} after trade: {trade_executor.risk_calculator.total_deposit_usdt} USDT")
                    except ccxt.InvalidOrder as e:
                        logger_main.warning(f"Insufficient volume for trade on {symbol}: {str(e)}")
                        if user_id not in trade_errors:
                            trade_errors[user_id] = []
                        trade_errors[user_id].append(f"Insufficient volume for trade on {symbol}: {str(e)}")
                        # Кэшируем проблемный символ
                        await add_to_problematic_symbols(symbol, ex_name)
                        continue
                    except Exception as e:
                        logger_main.error(f"Error processing symbol {symbol} for {user_id} on {ex_name}: {str(e)}")
                        logger_exceptions.error(f"Error processing symbol {symbol}: {str(e)}", exc_info=True)
                        if user_id not in trade_errors:
                            trade_errors[user_id] = []
                        trade_errors[user_id].append(f"Error processing symbol {symbol}: {str(e)}")
                        # Кэшируем проблемный символ
                        await add_to_problematic_symbols(symbol, ex_name)
                        continue
            except Exception as e:
                logger_main.error(f"Error processing symbol {symbol} for {user_id} on {ex_name}: {str(e)}")
                logger_exceptions.error(f"Error processing symbol {symbol}: {str(e)}", exc_info=True)
                if user_id not in trade_errors:
                    trade_errors[user_id] = []
                trade_errors[user_id].append(f"Error processing symbol {symbol}: {str(e)}")
                # Кэшируем проблемный символ
                await add_to_problematic_symbols(symbol, ex_name)
                continue
    except Exception as e:
        logger_main.error(f"Error processing symbols for {user_id} on {ex_name}: {str(e)}")
        logger_exceptions.error(f"Error processing symbols: {str(e)}", exc_info=True)
        if user_id not in trade_errors:
            trade_errors[user_id] = []
        trade_errors[user_id].append(f"Error processing symbols: {str(e)}")

def get_trade_errors(user_id):
    """Получение ошибок для пользователя"""
    if user_id in trade_errors and trade_errors[user_id]:
        return "\n".join(trade_errors[user_id][-10:])
    return "No errors to display."

__all__ = ['start_trading', 'get_trade_errors']
