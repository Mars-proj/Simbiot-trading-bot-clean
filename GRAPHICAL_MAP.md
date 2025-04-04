# Graphical Map of Trading Bot Project

## Core Modules
- main.py (Updated to support three users in April 2025)
- data_collector.py
- exchange_pool.py
- config_keys.py (Updated to load API keys from .env in April 2025)
- logging_setup.py

## Trading Modules
- trade_pool_core.py
- trade_pool_manager.py
- trade_pool_queries.py
- position_monitor.py
- start_trading_all.py
- trade_executor_core.py
- trade_executor_signals.py
- trading_cycle.py

## Data Collection and Analysis
- historical_data_fetcher.py
- ohlcv_fetcher.py
- ohlcv_analyzer.py
- data_utils.py
- market_analyzer.py
- market_rentgen_core.py
- market_trend_checker.py
- token_analyzer.py
- token_potential_evaluator.py
- trade_analyzer.py

## Machine Learning
- ml_data_preparer.py
- ml_data_preparer_utils.py
- ml_model_trainer.py
- ml_predictor.py
- model_utils.py
- retraining_manager.py
- test_retraining_manager.py
- features.py

## Symbol Management
- symbol_filter.py
- symbol_handler.py
- symbol_trade_processor.py
- symbol_data_fetcher.py
- test_symbols.py

## Signal Generation
- signal_generator_core.py
- signal_generator_dynamic.py
- signal_generator_indicators.py
- signal_blacklist.py
- indicators.py

## Risk and Position Management
- risk_manager.py
- position_monitor.py
- limits.py
- partial_close_calculator.py
- exit_points_calculator.py
- balance_manager.py
- deposit_calculator.py
- deposit_manager.py

## Utilities
- utils.py
- json_handler.py
- redis_client.py
- cache_utils.py
- global_objects.py
- notification_manager.py

## API and Exchange Integration
- api_server.py
- exchange_factory.py
- exchange_utils.py
- bot_user_data.py
- bot_trading.py

## Testing and Optimization
- backtest_cycle.py
- check_all_trades.py
- load_test.py
- local_model_api.py
- strategies.py
- monetization.py

## Worker and Background Tasks
- worker.py

## Total Modules: 67
