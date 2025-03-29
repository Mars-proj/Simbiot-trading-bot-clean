# Project Map for Trading Bot

## Key Values
- **BASE_MAX_SYMBOLS**: 100 (defined in `symbol_filter.py`)
- **BATCH_SIZE**: 50 (defined in `symbol_filter.py`)
- **MAX_SPREAD_PERCENT**: 0.01 (defined in `symbol_filter.py`)
- **max_recent_trades**: 10000 (defined in `trade_pool.py`)
- **ttl_seconds**: 604800 (defined in `trade_pool.py`)
- **max_concurrent_requests**: 10 (defined in `async_balance_fetcher.py`)
- **min_concurrent_requests**: 1 (defined in `async_balance_fetcher.py`)
- **max_users_concurrent**: 10 (defined in `trading_cycle.py`)
- **max_consecutive_errors**: 5 (defined in `trading_cycle.py`)
- **MAX_CACHE_SIZE**: 1000 (defined in `ohlcv_fetcher.py`)
- **CACHE_TTL**: 300 (defined in `data_fetcher.py`)

## Module List
Total modules: 102
- `analytics.py`
- `async_balance_fetcher.py`
- `async_exchange_manager.py`
- `async_ohlcv_fetcher.py`
- `async_order_fetcher.py`
- `async_ticker_fetcher.py`
- `async_utils.py`
- `backtest_analyzer.py`
- `backtest_cycle.py`
- `backtester.py`
- `balance_manager.py`
- `balance_utils.py`
- `bot_commands.py`
- `bot_trading.py`
- `bot_translations.py`
- `bot_user_data.py`
- `cache_utils.py`
- `check_all_trades.py`
- `check_balance.py`
- `check_balance_user1.py`
- `check_trades.py`
- `config.py`
- `data_fetcher.py`
- `data_utils.py`
- `deposit_calculator.py`
- `deposit_manager.py`
- `exchange_factory.py`
- `exchange_setup.py`
- `exchange_utils.py`
- `exit_points_calculator.py`
- `features.py`
- `global_objects.py`
- `holdings_manager.py`
- `indicators.py`
- `json_handler.py`
- `limits.py`
- `logging_setup.py`
- `manual_trade.py`
- `market_analyzer.py`
- `market_data_fetcher.py`
- `market_rentgen_core.py`
- `market_trend_checker.py`
- `ml_data_preparer.py`
- `ml_data_preparer_utils.py`
- `ml_data_preprocessor.py`
- `ml_feature_engineer.py`
- `ml_model_trainer.py`
- `ml_predictor.py`
- `model_utils.py`
- `momentum_indicators.py`
- `notification_utils.py`
- `ohlcv_analyzer.py`
- `ohlcv_fetcher.py`
- `order_utils.py`
- `partial_close_calculator.py`
- `position_monitor.py`
- `price_volatility_indicators.py`
- `price_volume_indicators.py`
- `redis_client.py`
- `retraining_data_preprocessor.py`
- `retraining_engine.py`
- `risk_manager.py`
- `signal_aggregator.py`
- `signal_blacklist.py`
- `signal_generator.py`
- `state.py`
- `strategies_momentum.py`
- `strategies_support_resistance.py`
- `strategies_trend.py`
- `strategies_volatility.py`
- `strategies_volume.py`
- `strategy_recommender.py`
- `symbol_data_fetcher.py`
- `symbol_filtering.py`
- `symbol_filter.py`
- `symbol_handler.py`
- `symbol_processor.py`
- `symbol_trade_processor.py`
- `symbol_utils.py`
- `telegram_bot.py`
- `test_symbols.py`
- `token_potential_evaluator.py`
- `trade_analyzer.py`
- `trade_blacklist.py`
- `trade_executor_core.py`
- `trade_executor_signals.py`
- `trade_pool_file.py`
- `trade_pool.py`
- `trade_pool_redis.py`
- `trade_pool_tokens.py`
- `trade_result_analyzer.py`
- `trade_risk_calculator.py`
- `trading_cycle.py`
- `trading_part1.py`
- `trend_indicators.py`
- `user_exchange_setup.py`
- `user_trade_cache.py`
- `utils.py`
- `websocket_manager.py`
- `worker.py`

## System Structure
### Core Modules
- **`trading_part1.py`** (Entry point)
  - Imports: `trading_cycle.py` (`main`), `trade_pool.py` (`TradePool`), `redis_client.py` (`RedisClient`), `global_objects.py` (to initialize `global_trade_pool` and `redis_client`)
  - Dependencies: `logging_setup.py` (for `initialize_loggers`)

- **`trading_cycle.py`** (Main trading loop)
  - Imports: `symbol_handler.py` (`process_symbols`), `global_objects.py` (`global_trade_pool`), `trade_executor_core.py` (`TradeExecutor`), `trade_executor_signals.py` (`generate_signal`, `execute_trade`), `config.py` (`API_KEYS`, `PREFERRED_EXCHANGES`)
  - Dependencies: `logging_setup.py` (`logger_main`)

- **`trade_executor_core.py`** (Trade executor core functionality)
  - Imports: `logging_setup.py` (`logger_main`), `async_ohlcv_fetcher.py` (`AsyncOHLCVFetcher`), `deposit_manager.py` (`DepositManager`), `market_data_fetcher.py` (`MarketDataFetcher`), `trade_risk_calculator.py` (`TradeRiskCalculator`)
  - Used in: `trading_cycle.py`

- **`trade_executor_signals.py`** (Trade signal generation and execution)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `signal_generator.py` (`generate_signals`), `global_objects.py` (`global_trade_pool`), `config.py` (`get_backtest_settings`)
  - Used in: `symbol_trade_processor.py`

### Data Fetching
- **`async_ohlcv_fetcher.py`** (OHLCV data fetching)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`redis_client`)
  - Used in: `ohlcv_fetcher.py`, `ml_data_preparer.py`, `trade_executor_core.py`

- **`ohlcv_fetcher.py`** (OHLCV data wrapper)
  - Imports: `logging_setup.py` (`logger_main`), `async_ohlcv_fetcher.py` (`AsyncOHLCVFetcher`)
  - Used in: `symbol_handler.py`

- **`market_data_fetcher.py`** (Market data fetching, e.g., tickers)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`redis_client`)
  - Used in: `trade_executor_core.py`

- **`data_fetcher.py`** (General data fetching with caching)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `symbol_utils.py` (`compress_ohlcv`)
  - Used in: `trade_result_analyzer.py`

- **`async_balance_fetcher.py`** (Balance fetching)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`)
  - Used in: None (not directly referenced, may be used in other modules)

### Trade Management
- **`deposit_manager.py`** (Balance and deposit management)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`redis_client`, `global_trade_pool`)
  - Used in: `trade_executor_core.py`, `trade_risk_calculator.py`

- **`trade_risk_calculator.py`** (Risk calculation and trade percentage)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`global_trade_pool`)
  - Used in: `trade_executor_core.py`

- **`trade_pool.py`** (Trade storage)
  - Imports: `trade_pool_redis.py`, `trade_pool_file.py`, `trade_pool_tokens.py`, `user_trade_cache.py` (`UserTradeCache`), `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `config.py` (`LOGGING_SETTINGS`)
  - Used in: `global_objects.py` (for `global_trade_pool`)

- **`trade_pool_redis.py`** (Redis storage for trades)
  - Imports: `logging_setup.py` (`logger_main`, `logger_trade_pool`), `utils.py` (`log_exception`), `json_handler.py` (`dumps`, `loads`)
  - Used in: `trade_pool.py`

- **`trade_pool_file.py`** (File storage for trades)
  - Imports: `logging_setup.py` (`logger_main`, `logger_trade_pool`), `utils.py` (`log_exception`), `json_handler.py` (`dumps`)
  - Used in: `trade_pool.py`

- **`trade_pool_tokens.py`** (Token management for trades)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `json_handler.py` (`dumps`, `loads`)
  - Used in: `trade_pool.py`

- **`user_trade_cache.py`** (Per-user trade cache)
  - Imports: `global_objects.py` (`redis_client`), `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `json_handler.py` (`dumps`, `loads`)
  - Used in: `trade_pool.py`

- **`trade_analyzer.py`** (Trade analysis)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `trade_pool.py` (`global_trade_pool`), `redis_client.py` (`redis_client`)
  - Used in: None (not directly referenced, may be used in other modules)

- **`trade_result_analyzer.py`** (Trade result analysis and retraining)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `data_fetcher.py` (`fetch_ticker_cached`), `redis_client.py` (`redis_client`)
  - Used in: None (not directly referenced, may be used in other modules)

### Symbol Processing
- **`symbol_handler.py`** (Symbol processing orchestration)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `symbol_filter.py` (`filter_symbols`), `ohlcv_fetcher.py` (`fetch_ohlcv_with_cache`, `symbol_data_cache`), `trade_executor_signals.py` (`execute_trade`)
  - Used in: `trading_cycle.py`

- **`symbol_filter.py`** (Symbol filtering)
  - Imports: `global_objects.py` (`global_trade_pool`, `redis_client`)
  - Used in: `symbol_handler.py`

- **`symbol_trade_processor.py`** (Symbol trade processing)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `market_rentgen_core.py` (`market_rentgen`), `global_objects.py` (`global_trade_pool`), `trade_executor_signals.py` (`execute_trade`)
  - Used in: `symbol_handler.py`

### Signal Generation and Strategy
- **`signal_generator.py`** (Signal generation)
  - Imports: `global_objects.py` (`redis_client`, `global_trade_pool`)
  - Used in: `trade_executor_signals.py`

- **`market_rentgen_core.py`** (Market analysis and strategy recommendation)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`global_trade_pool`), `ml_predictor.py` (`ml_predictor`, `initialize_ml_predictor`), `strategy_recommender.py` (`StrategyRecommender`)
  - Used in: `symbol_trade_processor.py`

- **`strategy_recommender.py`** (Strategy recommendation)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`global_trade_pool`, `redis_client`)
  - Used in: `market_rentgen_core.py`

### Machine Learning
- **`ml_data_preparer.py`** (Data preparation for ML)
  - Imports: `backtester.py` (`Backtester`), `async_ohlcv_fetcher.py` (`AsyncOHLCVFetcher`), `global_objects.py` (`redis_client`)
  - Used in: `market_rentgen_core.py`

- **`ml_predictor.py`** (ML prediction)
  - Imports: `logging_setup.py` (`logger_main`), `retraining_engine.py` (`RetrainEngine`)
  - Used in: `market_rentgen_core.py`

- **`retraining_engine.py`** (Model retraining)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`), `global_objects.py` (`global_trade_pool`), `retraining_data_preprocessor.py` (`RetrainDataPreprocessor`)
  - Used in: `ml_predictor.py`

- **`retraining_data_preprocessor.py`** (Data preprocessing for retraining)
  - Imports: `logging_setup.py` (`logger_main`), `utils.py` (`log_exception`)
  - Used in: `retraining_engine.py`

- **`backtester.py`** (Backtesting)
  - Imports: `strategies_support_resistance.py` (`generate_support_resistance_signals`)
  - Used in: `ml_data_preparer.py`

- **`strategies_support_resistance.py`** (Support/Resistance strategy)
  - Imports: `global_objects.py` (`redis_client`, `global_trade_pool`)
  - Used in: `backtester.py`

### Utilities
- **`utils.py`** (General utilities)
  - Exports: `log_exception`
  - Used in: Almost all modules

- **`logging_setup.py`** (Logging setup)
  - Exports: `logger_main`, `logger_trade_pool`, `logger_exceptions`
  - Used in: `trading_part1.py`, `trade_pool_redis.py`, `trade_pool_file.py`, `trade_pool_tokens.py`, `utils.py`

- **`global_objects.py`** (Global objects)
  - Exports: `global_trade_pool`, `redis_client`
  - Used in: Many modules

- **`config.py`** (Configuration)
  - Exports: `get_dynamic_symbol_criteria`, `get_backtest_settings`, `LOGGING_SETTINGS`
  - Used in: `ml_data_preparer.py`, `trade_executor_signals.py`, `trade_pool.py`

- **`json_handler.py`** (JSON handling)
  - Imports: `json`, `pandas`, `numpy`
  - Used in: `trade_pool_redis.py` (`dumps`, `loads`), `trade_pool_file.py` (`dumps`), `trade_pool_tokens.py` (`dumps`, `loads`)

## Current Tasks
- **Add per-user trade caching**:
  - Created `user_trade_cache.py` to manage per-user trade caches.
  - Updated `trade_pool.py` to integrate with `UserTradeCache`.
- **Fix logging initialization issues**:
  - Updated `logging_setup.py` to return success status from `initialize_loggers`.
  - Updated `trading_part1.py` to check success of logger initialization and exit if it fails.
  - Updated `utils.py` to remove `logger_main` from module-level imports and use local imports in functions.
  - Updated all modules to import `logger_main` from `logging_setup.py` instead of `utils.py`.
- **Split `trade_executor.py` into smaller modules**:
  - Split into `trade_executor_core.py` (core functionality) and `trade_executor_signals.py` (signal generation and trade execution).
  - Updated `trading_cycle.py` and `symbol_trade_processor.py` to use new modules.
- **Next Steps**:
  - Restart the system and check for issues.
  - Integrate selective data extraction for AI and backtesting using `UserTradeCache`.
  - Continue optimization and add new features for self-learning and self-development.
