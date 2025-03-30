# Project Map: Trading Logic

## Overview
This file serves as the central hub for the trading bot project, providing a comprehensive overview of the system, its modules, their dependencies, and the roadmap for development, maintenance, and optimization.

## System Architecture
- **Core Trading Logic** (16 modules):
  - `trade_executor_core.py`: Executes trades based on signals (updated 2025-03-30: added input validation, improved logging, error handling, market order support, risk management, test mode support).
  - `trade_executor_signals.py`: Processes trading signals (updated 2025-03-29: added signal aggregation).
  - `bot_trading.py`: Main trading bot logic (updated 2025-03-30: integrated real signal generation, added input validation, improved logging, risk management, test mode support).
  - `start_trading_all.py`: Initiates trading for all symbols (updated 2025-03-30: added input validation, improved logging, error handling, risk management, test mode support).
  - `signal_generator_core.py`: Core signal generation logic.
  - `signal_generator_indicators.py`: Generates signals using indicators (updated 2025-03-30: added GPU support with cupy).
  - `strategies.py`: Defines trading strategies (updated 2025-03-29: merged support/resistance and recommendation logic).
  - `trade_pool_core.py`: Manages the trade pool (updated 2025-03-30: added in-memory caching, problematic symbol check).
  - `trade_pool_queries.py`: Queries trade pool data (updated 2025-03-29: added trade saving functionality).
  - `global_objects.py`: Global objects and configurations.
  - `symbol_filter.py`: Filters symbols for trading (updated 2025-03-29: consolidated symbol filtering).
  - `balance_manager.py`: Manages user balances (updated 2025-03-29: added holdings functionality).
  - `deposit_calculator.py`: Calculates deposit requirements.
  - `signal_blacklist.py`: Manages blacklisted signals.
  - `retraining_manager.py`: Manages model retraining (updated 2025-03-30: added error handling for data loading).
  - `local_model_api.py`: Local API for model inference (updated 2025-03-30: added GPU support with torch).

- **Supporting Modules** (7 modules):
  - `logging_setup.py`: Logging configuration.
  - `config_keys.py`: API key management (updated 2025-03-29: merged general settings).
  - `redis_client.py`: Redis client operations (updated 2025-03-29: merged initialization logic).
  - `json_handler.py`: JSON serialization/deserialization.
  - `backtest_cycle.py`: Backtesting cycle.
  - `bot_user_data.py`: User data management (updated 2025-03-29: added status functionality).
  - `api_server.py`: API server for external access (updated 2025-03-30: added API key authentication and rate limiting).

- **Additional Modules** (31 modules):
  - `cache_utils.py`: Caching utilities (updated 2025-03-30: added problematic symbol check).
  - `check_all_trades.py`: Checks all trades (updated 2025-03-30: added API key validation, improved logging, symbol validation).
  - `data_utils.py`: Data utilities (updated 2025-03-29: added input validation and improved logging).
  - `deposit_manager.py`: Manages deposits (updated 2025-03-30: added API key validation, symbol validation, improved logging).
  - `exchange_factory.py`: Exchange factory for creating exchange instances (updated 2025-03-30: improved logging, added support for additional parameters, added rate limit monitoring for MEXC).
  - `exchange_utils.py`: Exchange utilities (updated 2025-03-30: added input validation, improved logging).
  - `exit_points_calculator.py`: Calculates exit points for trades (updated 2025-03-29: added input validation and improved logging).
  - `features.py`: Feature engineering for ML models (updated 2025-03-29: added input validation, fixed RSI calculation, improved logging).
  - `indicators.py`: Technical indicators (updated 2025-03-29: added input validation, improved logging, merged momentum_indicators, price_volatility_indicators, price_volume_indicators, trend_indicators).
  - `limits.py`: Trading limits (updated 2025-03-30: improved for risk management integration).
  - `market_rentgen_core.py`: Core market analysis logic (updated 2025-03-29: added data validation and improved logging).
  - `market_trend_checker.py`: Checks market trends (updated 2025-03-29: added input validation and improved logging).
  - `ml_data_preparer.py`: Prepares data for ML models (updated 2025-03-29: added input validation, improved logging, merged retraining_data_preprocessor functionality).
  - `ml_data_preparer_utils.py`: Utilities for ML data preparation (updated 2025-03-29: added input validation and improved logging).
  - `ml_model_trainer.py`: Trains ML models (updated 2025-03-29: added input validation and improved logging).
  - `ml_predictor.py`: Makes predictions using ML models (updated 2025-03-29: added input validation and improved logging).
  - `model_utils.py`: Model utilities (updated 2025-03-29: added file validation and improved logging).
  - `monetization.py`: Monetization logic (updated 2025-03-29: added input validation and improved logging).
  - `ohlcv_analyzer.py`: OHLCV data analyzer (updated 2025-03-29: added input validation and improved logging).
  - `ohlcv_fetcher.py`: Fetches OHLCV data (updated 2025-03-29: added symbol validation and improved logging).
  - `order_utils.py`: Order utilities (updated 2025-03-30: added input validation, market order support, improved logging).
  - `partial_close_calculator.py`: Calculates partial closes (updated 2025-03-29: added input validation and improved logging).
  - `position_monitor.py`: Monitors positions.
  - `risk_manager.py`: Risk management (updated 2025-03-29: merged trade risk calculator).
  - `symbol_data_fetcher.py`: Fetches symbol data.
  - `symbol_handler.py`: Handles symbols (updated 2025-03-30: added symbol validation with load_markets).
  - `symbol_trade_processor.py`: Processes trades for symbols.
  - `test_symbols.py`: Test symbols.
  - `token_potential_evaluator.py`: Evaluates token potential.
  - `trade_analyzer.py`: Analyzes trades (updated 2025-03-29: merged trade result analyzer).
  - `trading_cycle.py`: Trading cycle logic (updated 2025-03-29: merged trading_part1).
  - `worker.py`: Worker for background tasks.
  - `utils.py`: General utilities.

- **Non-working Modules** (18 modules, physically present but marked as non-working):
  - `trade_blacklist.py`, `async_exchange_fetcher.py`, `market_analyzer.py`, `data_fetcher.py`, `symbol_utils.py`, `signal_aggregator.py`, `strategies_volume.py`, `holdings_manager.py`, `analytics.py`, `async_exchange_manager.py`, `async_order_fetcher.py`, `async_ticker_fetcher.py`, `async_utils.py`, `backtest_analyzer.py`, `backtester.py`, `balance_utils.py`, `bot_commands_balance.py`, `bot_commands_status.py`.
  - **Note (2025-03-29)**: The following modules are physically present in the repository but are marked as non-working and should not be used: `trade_blacklist.py`, `async_exchange_fetcher.py`, `market_analyzer.py`, `data_fetcher.py`, `symbol_utils.py`, `signal_aggregator.py`, `holdings_manager.py`, `analytics.py`, `async_exchange_manager.py`, `async_order_fetcher.py`, `async_ticker_fetcher.py`, `async_utils.py`, `backtest_analyzer.py`, `backtester.py`, `balance_utils.py`, `bot_commands_balance.py`, `bot_commands_status.py`, `async_ohlcv_fetcher.py`.

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
  - 2025-03-30: Added dependency `trade_executor_core -> limits` for risk management.
  - 2025-03-30: Added dependency `bot_trading -> limits` for risk management.
  - 2025-03-30: Added dependency `start_trading_all -> limits` for risk management.
  - 2025-03-30: Added dependency `check_all_trades -> symbol_handler`.
  - 2025-03-30: Added dependency `deposit_manager -> symbol_handler`.

## Roadmap
- **Short-term**:
  - Add additional security for API [Done: 2025-03-30].
  - Check caching of problematic symbols [Done: 2025-03-30].
  - Test real trading [Done: 2025-03-30].
  - Use GPU for calculations [Done: 2025-03-30].
  - Fix `retraining_manager.py` issue [Done: 2025-03-30].
  - Add API rate limit monitoring for MEXC [Done: 2025-03-30].
  - Load testing with 100 users.
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
