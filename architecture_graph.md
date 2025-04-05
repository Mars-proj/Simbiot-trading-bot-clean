# Архитектура системы Trading Bot

## Основные модули и зависимости

- **core.py**
  - Основной модуль, точка входа (`main`, `process_users`).
  - Зависимости: `exchange_pool.py`, `market_state_analyzer.py`, `symbol_filter.py`, `trading_manager.py`, `backtest_manager.py`, `test_symbols.py`, `bot_user_data.py`, `start_trading_all.py`.

- **market_state_analyzer.py**
  - Анализ состояния рынка (`analyze_market_state`, `calculate_dynamic_thresholds`).
  - Зависимости: `historical_data_fetcher.py`, `market_analyzer.py`, `market_rentgen_core.py`, `exchange_pool.py`.

- **symbol_filter.py**
  - Фильтрация и категоризация символов (`categorize_symbols`, `filter_symbols`).
  - Зависимости: `historical_data_fetcher.py`, `market_analyzer.py`, `market_rentgen_core.py`, `cache_manager.py`, `exchange_pool.py`.

- **backtest_manager.py**
  - Управление бэктестами (`run_backtests`).
  - Зависимости: `start_trading_all.py`.

- **trading_manager.py**
  - Управление торговлей для пользователя (`run_trading_for_user`).
  - Зависимости: `start_trading_all.py`, `trade_pool_manager.py`, `position_monitor.py`, `retraining_manager.py`, `historical_data_fetcher.py`, `ml_data_preparer.py`, `data_collector.py`, `ml_model_trainer.py`, `symbol_filter.py`, `exchange_pool.py`.

- **cache_manager.py**
  - Управление кэшем символов (`load_symbol_cache`, `save_symbol_cache`).
  - Зависимости: нет.

- **historical_data_fetcher.py**
  - Загрузка исторических данных с CoinGecko и биржи.
  - Зависимости: `cache_manager.py`, `exchange_pool.py`.

- **exchange_pool.py**
  - Управление подключениями к бирже.
  - Зависимости: `bot_user_data.py`.

- **market_analyzer.py**
  - Анализ рыночных данных (волатильность, тренды).
  - Зависимости: нет.

- **market_rentgen_core.py**
  - Глубокий анализ рынка (настроение, всплески объёма).
  - Зависимости: нет.

- **start_trading_all.py**
  - Запуск торговли.
  - Зависимости: нет.

- **trade_pool_manager.py**
  - Управление пулом сделок.
  - Зависимости: нет.

- **position_monitor.py**
  - Мониторинг позиций.
  - Зависимости: нет.

- **retraining_manager.py**
  - Управление переобучением модели.
  - Зависимости: нет.

- **bot_user_data.py**
  - Управление данными пользователя.
  - Зависимости: нет.

- **test_symbols.py**
  - Тестовые символы для торговли.
  - Зависимости: `exchange_pool.py`.

## Удалённые модули
- `main.py` (удалён в рамках рефакторинга, заменён на `core.py` и другие модули).
