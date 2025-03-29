import asyncio
import pandas as pd
from logging_setup import logger_main, logger_exceptions

class Backtester:
    def __init__(self):
        self.initial_balance = 1000.0  # Начальный баланс для бэктестинга (USDT)
        self.trade_amount_percentage = 0.1  # Процент от баланса для каждой сделки

    def run_backtest(self, df, strategy, trade_amount_percentage=None):
        """Выполняет бэктестинг на основе исторических данных и стратегии"""
        if df.empty:
            logger_main.warning("DataFrame is empty, cannot run backtest")
            return None

        balance = self.initial_balance
        position = 0  # Количество токенов в позиции
        trades = []
        trade_amount = balance * (trade_amount_percentage or self.trade_amount_percentage)

        for i in range(1, len(df)):
            signal = self._get_signal(strategy, df.iloc[:i])
            price = df['close'].iloc[i]

            if signal == 1 and position == 0:  # Buy
                amount = trade_amount / price
                position += amount
                balance -= trade_amount
                trades.append({'type': 'buy', 'price': price, 'amount': amount, 'balance': balance})

            elif signal == -1 and position > 0:  # Sell
                balance += position * price
                trades.append({'type': 'sell', 'price': price, 'amount': position, 'balance': balance})
                position = 0

        # Рассчитываем результаты
        final_balance = balance + (position * df['close'].iloc[-1] if position > 0 else 0)
        profit_percentage = ((final_balance - self.initial_balance) / self.initial_balance) * 100
        max_drawdown = self._calculate_max_drawdown(trades)

        return {
            'profit_percentage': profit_percentage,
            'max_drawdown': max_drawdown,
            'final_balance': final_balance,
            'trades': trades
        }

    def _get_signal(self, strategy, df):
        """Получает сигнал от стратегии"""
        if strategy == 'MovingAverageStrategy':
            if len(df) < 20:  # Простая проверка на достаточность данных
                return 0
            short_ma = df['close'].rolling(window=10).mean().iloc[-1]
            long_ma = df['close'].rolling(window=20).mean().iloc[-1]
            return 1 if short_ma > long_ma else -1 if short_ma < long_ma else 0
        elif strategy == 'RSIDivergenceStrategy':
            if len(df) < 14:
                return 0
            rsi = self._calculate_rsi(df['close'], 14)
            return -1 if rsi.iloc[-1] > 70 else 1 if rsi.iloc[-1] < 30 else 0
        elif strategy == 'BollingerBandsBreakoutStrategy':
            if len(df) < 20:
                return 0
            bb = self._calculate_bollinger_bands(df['close'], 20)
            price = df['close'].iloc[-1]
            return 1 if price > bb['upper'].iloc[-1] else -1 if price < bb['lower'].iloc[-1] else 0
        elif strategy == 'MACDTrendFollowingStrategy':
            if len(df) < 26:
                return 0
            macd, signal = self._calculate_macd(df['close'])
            return 1 if macd.iloc[-1] > signal.iloc[-1] else -1 if macd.iloc[-1] < signal.iloc[-1] else 0
        return 0

    def _calculate_rsi(self, prices, period=14):
        """Рассчитывает RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Рассчитывает Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return pd.DataFrame({'middle': sma, 'upper': upper, 'lower': lower})

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Рассчитывает MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

    def _calculate_max_drawdown(self, trades):
        """Рассчитывает максимальную просадку"""
        if not trades:
            return 0.0
        balances = [trade['balance'] for trade in trades]
        peak = balances[0]
        max_drawdown = 0.0
        for balance in balances:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak
            max_drawdown = max(max_drawdown, drawdown)
        return max_drawdown

async def run_backtest(exchange, backtester, filtered_symbols, strategies):
    """Выполняет бэктестинг для всех стратегий на указанных символах"""
    logger_main.info("Запуск бэктестинга")
    backtest_results = {}
    total_symbols = len(filtered_symbols[:50])  # Считаем общее количество символов
    backtester = Backtester()  # Создаём объект Backtester

    for idx, symbol in enumerate(filtered_symbols[:50], 1):  # Добавляем индекс для отслеживания прогресса
        logger_main.info(f"Запуск бэктестинга для символа {symbol} ({idx}/{total_symbols})")
        try:
            logger_main.debug(f"Получение OHLCV-данных для {symbol}")
            ohlcv = await asyncio.wait_for(exchange.fetch_ohlcv(symbol, timeframe='1h', limit=1000), timeout=30)
            if not ohlcv:
                logger_main.warning(f"Не удалось загрузить OHLCV-данные для {symbol}")
                continue
            logger_main.debug(f"OHLCV-данные для {symbol} успешно получены, длина: {len(ohlcv)}")
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logger_main.debug(f"DataFrame для {symbol} создан")
            backtest_results[symbol] = {}
            total_strategies = len(strategies)  # Считаем общее количество стратегий
            for strat_idx, strategy in enumerate(strategies, 1):  # Добавляем индекс для стратегий
                logger_main.debug(f"Бэктестинг стратегии {strategy} для {symbol} ({strat_idx}/{total_strategies})")
                try:
                    result = backtester.run_backtest(df, strategy, trade_amount_percentage=0.1)
                    if result:
                        backtest_results[symbol][strategy] = result
                        logger_main.info(f"Результаты бэктестинга для {symbol} ({strategy}): прибыль={result['profit_percentage']:.2f}%, макс. просадка={result['max_drawdown']:.2f}")
                    else:
                        logger_main.warning(f"Бэктестинг для {symbol} ({strategy}) вернул пустой результат")
                except Exception as e:
                    logger_main.error(f"Ошибка при бэктестинге стратегии {strategy} для {symbol}: {str(e)}")
                    logger_exceptions.error(f"Ошибка при бэктестинге стратегии {strategy}: {str(e)}", exc_info=True)
        except asyncio.TimeoutError as e:
            logger_main.error(f"Тайм-аут при получении OHLCV-данных для {symbol}: {str(e)}")
            logger_exceptions.error(f"Тайм-аут при получении OHLCV-данных: {str(e)}", exc_info=True)
        except Exception as e:
            logger_main.error(f"Ошибка при бэктестинге для символа {symbol}: {str(e)}")
            logger_exceptions.error(f"Ошибка при бэктестинге: {str(e)}", exc_info=True)
    logger_main.debug("Бэктестинг завершён")
    return backtest_results

__all__ = ['run_backtest']
