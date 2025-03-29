import asyncio
import time
from balance_manager import BalanceManager
from deposit_calculator import DepositCalculator
from signal_blacklist import SignalBlacklist
from logging_setup import logger_main, logger_exceptions
from json_handler import loads

class TradeExecutor:
    def __init__(self, max_drawdown=0.2):
        self.balance_manager = BalanceManager()
        self.deposit_calculator = None  # Инициализируем позже в initialize_deposit
        self.signal_blacklist = SignalBlacklist()
        self.risk_calculator = None  # Инициализируем позже
        self.trade_stats = {
            'total_pnl': 0,
            'successful_trades': 0,
            'trade_history': [],
            'current_deposit': 0
        }
        self.can_buy = True  # Флаг, разрешающий покупки
        self.holdings = {}  # Словарь: {base_asset: {'trade_id': ..., 'price': ...}}
        self.min_trade_amount_usdt = 10.03  # Минимальная сумма сделки (10 USDT + 0.3% комиссии)
        self.min_volume_usdt = 1.0  # Минимальный объём сделки для MEXC (1 USDT)
        self.max_trade_amount_usdt = 100.0  # Начальная максимальная сумма сделки (будет динамически изменяться)
        self.balance_safety_margin = 1.1  # Запас 10% для учёта скрытых комиссий
        self.confidence_threshold = 0.8  # Порог уверенности для увеличения суммы сделки (80%)
        self.max_trade_multiplier = 5.0  # Максимальный множитель для суммы сделки при высокой уверенности
        self.volatility_adjustment_factor = 0.5  # Коэффициент корректировки суммы сделки на основе волатильности
        self.recent_trades = {}  # Хранит недавние сделки для предотвращения повторных покупок: {user_id: {symbol: timestamp}}
        self.trade_cooldown = 3600  # Время в секундах (1 час) до повторной покупки того же токена
        logger_main.debug("TradeExecutor инициализирован (без загрузки позиций из Redis)")

    async def initialize(self):
        """Инициализация, включая загрузку открытых позиций из Redis"""
        logger_main.debug("Начало асинхронной инициализации TradeExecutor")
        await self._load_holdings_from_redis()
        logger_main.debug("Асинхронная инициализация TradeExecutor завершена")

    async def _load_holdings_from_redis(self):
        """Загружаем открытые позиции из Redis"""
        logger_main.info("Загрузка открытых позиций из Redis")
        try:
            trades = await global_trade_pool.get_all_trades()
            for trade in trades:
                if trade['side'] == 'buy' and trade['status'] in ['executed', 'filled']:
                    symbol = trade['symbol']
                    base_asset = symbol.split('/')[0]
                    if base_asset not in self.holdings:
                        self.holdings[base_asset] = {
                            'trade_id': trade.get('trade_id', 'unknown'),
                            'price': trade['price'],
                            'amount': trade['amount'],
                            'side': trade['side'],
                            'timestamp': trade['timestamp'],
                            'market_conditions': trade.get('market_conditions', {}),
                            'order_id': trade.get('order_id', 'unknown')
                        }
                        logger_main.info(f"Восстановлена открытая позиция из Redis: {base_asset} -> {self.holdings[base_asset]}")
        except Exception as e:
            logger_main.error(f"Ошибка при загрузке открытых позиций из Redis: {str(e)}")
            logger_exceptions.error(f"Ошибка при загрузке открытых позиций: {str(e)}", exc_info=True)

    def is_symbol_in_blacklist(self, symbol):
        """Проверяет, находится ли символ в чёрном списке"""
        return self.signal_blacklist.is_symbol_in_blacklist(symbol)

    async def fetch_balance_with_cache(self, exchange, user_id, force_refresh=False):
        """Получение баланса через BalanceManager (асинхронный вызов)"""
        return await self.balance_manager.fetch_balance_with_cache(exchange, user_id, force_refresh)

    async def initialize_deposit(self, exchange, user_id, unavailable_symbols=None):
        """Инициализация депозита через DepositCalculator"""
        logger_main.debug(f"Инициализация депозита для пользователя {user_id}")
        self.deposit_calculator = DepositCalculator(max_drawdown=0.2, user_id=user_id)
        self.risk_calculator = self.deposit_calculator  # Обновляем risk_calculator
        await self.deposit_calculator.calculate_total_deposit(exchange)
        # Устанавливаем начальный депозит
        initial_deposit = self.deposit_calculator.total_deposit_usdt
        self.trade_stats['current_deposit'] = initial_deposit
        logger_main.debug(f"TradeExecutor инициализирован с начальным депозитом: {initial_deposit} USDT для пользователя {user_id}")

    async def calculate_total_deposit(self, exchange):
        """Расчёт депозита через DepositCalculator"""
        if self.deposit_calculator is None:
            logger_main.error("DepositCalculator не инициализирован, вызовите initialize_deposit сначала")
            return 0.0
        await self.deposit_calculator.calculate_total_deposit(exchange)
        self.trade_stats['current_deposit'] = self.deposit_calculator.total_deposit_usdt
        return self.deposit_calculator.total_deposit_usdt

    async def check_drawdown(self, exchange):
        """Проверка просадки через DepositCalculator"""
        if self.deposit_calculator is None:
            logger_main.error("DepositCalculator не инициализирован, вызовите initialize_deposit сначала")
            return False
        return self.deposit_calculator.check_drawdown(exchange)

    def adjust_trade_amount(self, confidence, market_conditions, deposit, price, side):
        """Динамически корректирует сумму сделки на основе уверенности сигнала, рыночных условий и минимального объёма"""
        # Базовая сумма сделки
        base_amount = self.min_trade_amount_usdt
        # Увеличиваем сумму, если уверенность сигнала выше порога
        if confidence >= self.confidence_threshold:
            multiplier = min(self.max_trade_multiplier, 1 + (confidence - self.confidence_threshold) * 10)
            base_amount *= multiplier
            logger_main.debug(f"Increased trade amount due to high confidence ({confidence}): {base_amount} USDT")
        # Корректируем сумму на основе волатильности рынка
        if 'avg_volatility' in market_conditions:
            volatility = market_conditions['avg_volatility']
            # Если волатильность высокая, уменьшаем сумму для снижения риска
            volatility_adjustment = max(0.5, 1 - volatility * self.volatility_adjustment_factor)
            base_amount *= volatility_adjustment
            logger_main.debug(f"Adjusted trade amount for volatility ({volatility}): {base_amount} USDT")
        # Ограничиваем сумму максимальным значением, зависящим от депозита
        max_allowed = min(self.max_trade_amount_usdt, deposit * 0.1)  # Не более 10% депозита
        final_amount = min(base_amount, max_allowed)
        # Проверяем минимальный объём сделки (1 USDT для MEXC)
        amount = final_amount / price  # Переводим сумму в количество токенов
        value_usdt = amount * price  # Проверяем стоимость в USDT
        if value_usdt < self.min_volume_usdt:
            amount = self.min_trade_amount_usdt / price  # Увеличиваем количество токенов, чтобы сумма была >= 10.03 USDT
            final_amount = amount * price
            logger_main.debug(f"Adjusted trade amount to meet minimum volume requirement: {final_amount} USDT (amount: {amount})")
        # Убедимся, что сумма сделки не меньше минимального порога для покупки и продажи
        if final_amount < self.min_trade_amount_usdt:
            amount = self.min_trade_amount_usdt / price
            final_amount = amount * price
            logger_main.debug(f"Adjusted trade amount to meet minimum trade requirement ({self.min_trade_amount_usdt} USDT): {final_amount} USDT (amount: {amount})")
        logger_main.debug(f"Final trade amount after adjustments: {final_amount} USDT (max allowed: {max_allowed} USDT)")
        return amount

    def can_trade_symbol(self, user_id, symbol):
        """Проверяет, можно ли торговать данным символом (предотвращает повторные покупки)"""
        if user_id not in self.recent_trades:
            self.recent_trades[user_id] = {}
        if symbol in self.recent_trades[user_id]:
            last_trade_time = self.recent_trades[user_id][symbol]
            current_time = int(time.time())
            if current_time - last_trade_time < self.trade_cooldown:
                logger_main.warning(f"Cannot trade {symbol} for user {user_id}: on cooldown (last trade at {last_trade_time})")
                return False
        return True

    def record_trade(self, user_id, symbol):
        """Записывает сделку для предотвращения повторных покупок"""
        if user_id not in self.recent_trades:
            self.recent_trades[user_id] = {}
        self.recent_trades[user_id][symbol] = int(time.time())
        logger_main.debug(f"Recorded trade for user {user_id} on symbol {symbol}")

    async def execute_trade(self, exchange, trade, confidence, market_conditions):
        """Выполняет сделку на бирже с учётом динамической суммы"""
        # Проверяем, можно ли торговать данным символом
        if not self.can_trade_symbol(trade['user_id'], trade['symbol']):
            return None
        # Получаем текущий депозит
        deposit = await self.calculate_total_deposit(exchange)
        # Корректируем сумму сделки
        trade['amount'] = self.adjust_trade_amount(confidence, market_conditions, deposit, trade['price'], trade['side'])
        trade_amount_usdt = trade['amount'] * trade['price']
        logger_main.info(f"Executing trade for {trade['symbol']} with amount {trade['amount']} (value: {trade_amount_usdt} USDT)")
        # Проверяем баланс перед продажей
        if trade['side'] == 'sell':
            base_asset = trade['symbol'].split('/')[0]
            balance = await self.fetch_balance_with_cache(exchange, trade['user_id'])
            available = balance.get(base_asset, {}).get('free', 0)
            if available < trade['amount']:
                logger_main.warning(f"Cannot sell {trade['amount']} of {base_asset}: only {available} available")
                return None
        # Устанавливаем тип ордера на 'limit' (MEXC не поддерживает stop-limit через API)
        trade['order_type'] = 'limit'
        # Выполняем сделку
        try:
            order = await exchange.create_limit_order(
                trade['symbol'],
                trade['side'],
                trade['amount'],
                trade['price']
            )
            if order:
                self.record_trade(trade['user_id'], trade['symbol'])
                self.trade_stats['successful_trades'] += 1
                self.trade_stats['trade_history'].append(trade)
                logger_main.info(f"Order created: {order}")
                return order
            else:
                logger_main.warning(f"Failed to create order for {trade['symbol']}")
                return None
        except Exception as e:
            logger_main.error(f"Error executing trade for {trade['symbol']}: {str(e)}")
            logger_exceptions.error(f"Error executing trade: {str(e)}", exc_info=True)
            return None

__all__ = ['TradeExecutor']
