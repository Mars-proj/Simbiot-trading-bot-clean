# Graphical Map of Simbiot Trading Bot

## Module Dependencies
- main.py
  ├── start_trading_all.py
  │   ├── historical_data_fetcher.py
  │   ├── ml_predictor.py
  │   └── trade_executor_core.py
  ├── bot_user_data.py
  │   └── config_keys.py
  ├── test_symbols.py
  ├── trade_pool_manager.py
  │   └── trade_pool_core.py
  ├── position_monitor.py
  ├── retraining_manager.py (background task)
  │   ├── ml_data_preparer.py
  │   ├── historical_data_fetcher.py
  │   └── data_collector.py
  ├── exchange_pool.py
  ├── market_analyzer.py
  └── market_rentgen_core.py

## Data Flow
1. main.py -> process_users -> run_trading_for_user (async for all users)
2. run_trading_for_user -> filter_symbols -> market_analyzer -> market_rentgen_core -> start_trading_all
3. start_trading_all -> trade_symbol -> trade_executor_core
4. retraining_manager -> schedule_retraining (background) -> ml_data_preparer
