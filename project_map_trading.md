# Project Map: Trading Logic

## Overview
This file serves as the central hub for the trading bot project, providing a comprehensive overview of the system, its modules, their dependencies, and the roadmap for development, maintenance, and optimization.

## System Architecture
- **Core Trading Logic** (16 modules):
  - `trade_executor_core.py`: Executes trades based on signals (updated 2025-03-29: added user validation and improved logging).
  - `trade_executor_signals.py`: Processes trading signals.
  - `bot_trading.py`: Main trading bot logic (updated 2025-03-29: improved logging).
  - `start_trading_all.py`: Initiates trading for all symbols (updated 2025-03-29: improved logging).
  - `signal_generator_core.py`: Core signal generation logic.
  - `signal_generator_indicators.py`: Generates signals using indicators.
  - `strategies.py`: Defines trading strategies.
  - `trade_pool_core.py`: Manages the trade pool.
  - `trade_pool_queries.py`: Queries trade pool data.
  - `global_objects.py`: Global objects and configurations.
  - `symbol_filter.py`: Filters symbols for trading.
  - `balance_manager.py`: Manages user balances.
  - `deposit_calculator.py`: Calculates deposit requirements.
  - `signal_blacklist.py`: Manages blacklisted signals.
  - `retraining_manager.py`: Manages model retraining.
  - `local_model_api.py`: Local API for model inference.

- **Supporting Modules** (20 modules, 9 kept, 11 removed):
  - **Kept**:
    - `logging_setup.py`: Logging configuration.
    - `config_keys.py`: API key management.
    - `redis_initializer.py`: Redis initialization.
    - `redis_client.py`: Redis client operations.
    - `json_handler.py`: JSON serialization/deserialization.
    - `config_settings.py`: General configuration settings.
    - `backtest_cycle.py`: Backtesting cycle.
    - `bot_user_data.py`: User data management.
    - `api_server.py`: API server for external access.
  - **Removed**:
    - `manual_trade.py`, `async_balance_fetcher.py`, `websocket_manager.py`, `notification_manager.py`, `rate_limiter.py`, `error_handler.py`, `performance_metrics.py`, `user_manager.py`, `trade_history.py`, `market_data_fetcher.py`, `exchange_connection_settings.py`.

- **Additional Modules** (78 modules, 78 checked, 0 unchecked):
  - **Checked**:
    - **Kept** (35 modules):
      - `cache_utils.py`: Caching utilities (updated 2025-03-29: added default TTL and error handling).
      - `check_all_trades.py`: Checks all trades (updated 2025-03-29: added exchange validation and improved logging).
      - `check_trades.py`: Checks individual trades (updated 2025-03-29: added exchange validation and improved logging).
      - `data_utils.py`: Data utilities (updated 2025-03-29: added input validation and improved logging).
      - `deposit_manager.py`: Manages deposits (updated 2025-03-29: added exchange validation and improved logging).
      - `exchange_factory.py`: Exchange factory for creating exchange instances (updated 2025-03-29: added user validation and improved logging).
      - `exchange_setup.py`: Exchange setup utilities (updated 2025-03-29: improved logging).
      - `exchange_utils.py`: Exchange utilities (updated 2025-03-29: added symbol validation and improved logging).
      - `exit_points_calculator.py`: Calculates exit points for trades (updated 2025-03-29: added input validation and improved logging).
      - `features.py`: Feature engineering for ML models (updated 2025-03-29: added input validation, fixed RSI calculation, improved logging).
      - `indicators.py`: Technical indicators (updated 2025-03-29: added input validation and improved logging).
      - `limits.py`: Trading limits (updated 2025-03-29: added input validation and improved logging).
      - `market_rentgen_core.py`: Core market analysis logic (updated 2025-03-29: added data validation and improved logging).
      - `market_trend_checker.py`: Checks market trends (updated 2025-03-29: added input validation and improved logging).
      - `ml_data_preparer.py`: Prepares data for ML models (updated 2025-03-29: added input validation and improved logging).
      - `ml_data_preparer_utils.py`: Utilities for ML data preparation (updated 2025-03-29: added input validation and improved logging).
      - `ml_feature_engineer.py`: Feature engineering for ML (updated 2025-03-29: added input validation and improved logging).
      - `ml_model_trainer.py`: Trains ML models (updated 2025-03-29: added input validation and improved logging).
      - `ml_predictor.py`: Makes predictions using ML models (updated 2025-03-29: added input validation and improved logging).
      - `model_utils.py`: Model utilities (updated 2025-03-29: added file validation and improved logging).
      - `momentum_indicators.py`: Momentum indicators (updated 2025-03-29: added input validation and improved logging).
      - `monetization.py`: Monetization logic (updated 2025-03-29: added input validation and improved logging).
      - `ohlcv_analyzer.py`: OHLCV data analyzer (updated 2025-03-29: added input validation and improved logging).
      - `ohlcv_fetcher.py`: Fetches OHLCV data (updated 2025-03-29: added symbol validation and improved logging).
      - `order_utils.py`: Order utilities (updated 2025-03-29: added input validation and improved logging).
      - `partial_close_calculator.py`: Calculates partial closes (updated 2025-03-29: added input validation and improved logging).
      - `position_monitor.py`: Monitors positions.
      - `price_volatility_indicators.py`: Price volatility indicators.
      - `price_volume_indicators.py`: Price volume indicators.
      - `retraining_data_preprocessor.py`: Preprocesses data for retraining.
      - `retraining_engine.py`: Retraining engine.
      - `risk_manager.py`: Risk management.
      - `strategies_support_resistance.py`: Support and resistance strategies.
      - `strategy_recommender.py`: Recommends strategies.
      - `symbol_data_fetcher.py`: Fetches symbol data.
      - `symbol_filtering.py`: Symbol filtering utilities.
      - `symbol_handler.py`: Handles symbols.
      - `symbol_processor.py`: Processes symbols.
      - `symbol_trade_processor.py`: Processes trades for symbols.
      - `test_symbols.py`: Test symbols.
      - `token_potential_evaluator.py`: Evaluates token potential.
      - `trade_analyzer.py`: Analyzes trades.
      - `trade_pool_file.py`: File-based trade pool.
      - `trade_pool_global.py`: Global trade pool.
      - `trade_pool_redis.py`: Redis-based trade pool.
      - `trade_pool_tokens.py`: Token-based trade pool.
      - `trade_pool_transfer.py`: Transfers in trade pool.
      - `trade_result_analyzer.py`: Analyzes trade results.
      - `trade_risk_calculator.py`: Calculates trade risks.
      - `trading_cycle.py`: Trading cycle logic.
      - `trading_part1.py`: Part 1 of trading logic.
      - `trend_indicators.py`: Trend indicators.
      - `user_exchange_setup.py`: User exchange setup.
      - `user_trade_cache.py`: User trade cache.
      - `worker.py`: Worker for background tasks.
      - `utils.py`: General utilities.
    - **Removed** (28 modules):
      - `trade_blacklist.py`, `async_exchange_fetcher.py`, `market_analyzer.py`, `data_fetcher.py`, `symbol_utils.py`, `signal_aggregator.py`, `strategies_volume.py`, `holdings_manager.py`, `analytics.py`, `async_exchange_manager.py`, `async_order_fetcher.py`, `async_ticker_fetcher.py`, `async_utils.py`, `backtest_analyzer.py`, `backtester.py`, `balance_utils.py`, `bot_commands_balance.py`, `bot_commands_status.py`, `bot_commands_core.py`, `bot_translations.py`, `config_notifications.py`, `ml_data_preprocessor.py`, `notification_utils.py`, `async_ohlcv_fetcher.py`, `strategies_momentum.py`, `strategies_trend.py`, `strategies_volatility.py`, `state.py`.
  - **Unchecked**: 0 modules (all modules audited).

## Dependencies Graph
- See `trading_bot_graph.dot` for the dependency graph.
- Updates:
  - 2025-03-28: Removed dependency `json_handler -> logging_setup` (not found in code).
  - 2025-03-28: Added dependency `config_keys -> logging_setup`.
  - 2025-03-29: Removed dependency `bot_commands_core -> async_exchange_fetcher` (module removed).
  - 2025-03-29: Removed module `bot_commands_core.py` and its dependencies.
  - 2025-03-29: Removed module `bot_translations.py` and its dependencies.
  - 2025-03-29: Removed module `config_notifications.py` (no dependencies in graph).
  - 2025-03-29: Removed module `ml_data_preprocessor.py` (no dependencies in graph).
  - 2025-03-29: Removed module `notification_utils.py` (no dependencies in graph).
  - 2025-03-29: Removed module `trade_blacklist.py` (no dependencies in graph).

## Roadmap
- **Short-term**:
  - Fix errors in `trade_executor_core.py` (e.g., `logger_main` import).
  - Add additional security for API.
  - Check caching of problematic symbols.
  - Test real trading.
  - Use GPU for calculations.
  - Fix `retraining_manager.py` issue.
  - Add API rate limit monitoring for MEXC.
  - Load testing with 100 users.
  - Optimize `trade_executor_core.py`: Add input validation, risk management, and support for market orders.
  - Optimize `bot_trading.py`: Integrate real signal generation and risk management.
  - Optimize `start_trading_all.py`: Add input validation, risk management, and better error handling.
  - Optimize `check_all_trades.py` and `check_trades.py`: Add API key validation and detailed logging.
  - Optimize `deposit_manager.py`: Add API key validation and symbol validation.
  - Optimize `exchange_factory.py` and `exchange_setup.py`: Add support for additional configuration parameters.
  - Optimize `exchange_utils.py`: Add input validation for exchange object.
  - Optimize `order_utils.py`: Add support for market orders.
- **Medium-term**:
  - Scale to 1000+ users.
  - Implement self-learning and self-improving mechanisms.
  - Add support for more exchanges.
- **Long-term**:
  - Full market X-ray system.
  - Advanced ML model integration.
  - Cross-exchange arbitrage.

## Server Configuration
- **CPUs**: 2x Intel Xeon E5-2697A v4 (32 cores, 64 threads, ~2.4 TFLOPS FP32).
- **RAM**: 384 GB DDR4 (300 GB allocated to Redis, `maxmemory 300gb`).
- **Storage**:
  - 2x 480 GB SSD: OS and logs.
  - 1x 4 TB NVMe: Historical data.
- **Network**: 10 Gbit/s (optimized: `EXCHANGE_CONNECTION_SETTINGS.rateLimit` = 500 ms).
- **GPU**: NVIDIA Tesla T4 (16 GB GDDR6, 2560 CUDA cores, 8.1 TFLOPS FP32).
  - Used in `signal_generator_indicators.py` with `cupy`.
  - Used in `local_model_api.py` and `retraining_manager.py` with CUDA 12.1, cuDNN 8.9.7, PyTorch 2.5.1+cu121.
- **IP and Location**: 45.140.147.187 (Netherlands, nl-arenda.10).

## Audit Results
- See `project_map_audit_results.md` for detailed audit results.

## Code Modification Process
To ensure consistency and avoid errors during code modifications, the following process must be followed for each module update:

1. **Delete the old file**:
   - Command: `rm /root/trading_bot/<module_name>.py`
   - Example: `rm /root/trading_bot/bot_commands_core.py`

2. **Open nano to create the new file**:
   - Command: `nano /root/trading_bot/<module_name>.py`
   - Example: `nano /root/trading_bot/bot_commands_core.py`

3. **Insert the new code**:
   - Copy the updated code provided by Grok and paste it into nano.
   - Save the file (Ctrl+O, Enter, Ctrl+X).

4. **Add the updated file to Git index**:
   - Command: `git add <file> ...`
   - Example: `git add bot_commands_core.py`

5. **Create a commit**:
   - Command: `git commit -m "Update <module_name>.py by simbiot: <description>"`
   - Example: `git commit -m "Update bot_commands_core.py by simbiot: remove unused imports and add comment"`

6. **Push changes to GitHub**:
   - Command: `git push origin main`
   - This updates the repository directly from the server.

## Security Notes
- **2025-03-29**: Telegram bot token was compromised in `config_notifications.py` in the repository history. The token has been removed from the code and replaced with `os.getenv("TELEGRAM_BOT_TOKEN", "")`. A new token must be generated via BotFather and added to `.env`:
