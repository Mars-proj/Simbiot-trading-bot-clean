# Project Map: Trading Bot System

This file outlines the structure of the trading bot system, including Core Trading Logic, Supporting Modules, and Additional Modules. Each module is described with its purpose, dependencies, and status.

## Core Trading Logic
- `trade_executor_core.py`: Executes trades based on signals (updated 2025-04-01: added input validation, improved logging, error handling, test mode, removed placeholders, integrated `limits.py`, `exit_points_calculator.py`, `monetization.py`, `partial_close_calculator.py`, `risk_manager.py`, `symbol_handler.py`, `notification_manager.py`, added price validation 2025-04-01).
- `trade_executor_signals.py`: Processes trading signals (updated 2025-03-31: added signal aggregation with weights, made RSI thresholds configurable, integrated ML predictions via `local_model_api.py`, added moving averages and Bollinger Bands via `indicators.py`, added ML error handling 2025-04-01).
- `bot_trading.py`: Main trading bot logic (updated 2025-03-31: integrated `trade_executor_signals.py`, added input validation, improved logging, test mode, removed placeholders, added configurable trade percentage and RSI thresholds, integrated `deposit_calculator.py`, `signal_blacklist.py`, `bot_user_data.py`, `symbol_handler.py`, added signal validation 2025-04-01).
- `start_trading_all.py`: Starts trading for multiple symbols (updated 2025-03-31: added input validation, improved logging, error handling in `asyncio.gather`, test mode, removed placeholders, added configurable parameters, integrated `deposit_calculator.py`, `signal_blacklist.py`, `bot_user_data.py`, `symbol_handler.py`, improved logging 2025-04-01).

## Supporting Modules
- `api_server.py`: Provides API endpoints (updated 2025-03-31: added API key authentication, rate limiting, made API keys and rate limit configurable, improved rate limiting with time window).
- `backtest_cycle.py`: Handles backtesting (updated 2025-04-01: integrated `historical_data_fetcher.py` for historical data fetching, added result saving 2025-04-01).
- `bot_user_data.py`: Manages user data (updated 2025-03-31: made user data configurable, added API key validation, integrated into `bot_trading.py` and `start_trading_all.py`, added Redis persistence 2025-04-01).
- `cache_utils.py`: Caches symbol data (updated 2025-03-31: added check for problematic symbols before caching, made volume threshold and cache TTL configurable, added cache cleanup 2025-04-01).
- `check_all_trades.py`: Checks all trades (updated 2025-03-31: improved logging with trade types, removed placeholder for trade fetching, integrated `trade_pool_core.py`, `symbol_handler.py`, added status filtering 2025-04-01).
- `data_utils.py`: Utility functions for data handling (updated 2025-03-30: added data validation and normalization).
- `deposit_calculator.py`: Calculates required deposits (updated 2025-03-30: added configurable margin multiplier, added minimum deposit check 2025-04-01).
- `deposit_manager.py`: Manages deposits (updated 2025-03-31: improved logging with currency and balance info, added balance check via `balance_manager.py`, integrated `exchange_factory.py`, `symbol_handler.py`, replaced placeholder with API call 2025-04-01).
- `exchange_factory.py`: Creates exchange instances (updated 2025-03-31: made rateLimit and enableRateLimit configurable, added universal rate limit monitoring, added testnet support check, added rate limit monitoring for MEXC, improved logging, added support for additional configuration parameters).
- `exchange_utils.py`: Utility functions for exchange operations (updated 2025-03-31: improved logging with bid/ask data, added symbol validation via `symbol_handler.py`).
- `exit_points_calculator.py`: Calculates stop-loss and take-profit levels (updated 2025-03-31: integrated into `trade_executor_core.py`).
- `features.py`: Extracts features for ML models (updated 2025-03-31: made RSI period configurable, integrated into `ml_data_preparer.py`).
- `historical_data_fetcher.py`: Fetches historical OHLCV data for backtesting (added 2025-04-01: fetches historical data, converts to DataFrame, integrates with `backtest_cycle.py`, added pagination 2025-04-01).
- `indicators.py`: Calculates technical indicators (updated 2025-03-31: integrated into `trade_executor_signals.py` for moving averages and Bollinger Bands).
- `limits.py`: Manages risk limits (updated 2025-03-31: added total position size check, made parameters configurable, integrated into `trade_executor_core.py`, added per-symbol limit check 2025-04-01).
- `market_rentgen_core.py`: Analyzes market conditions (updated 2025-03-31: added trend and volatility analysis, added symbol validation via `symbol_handler.py`).
- `market_trend_checker.py`: Checks market trends (updated 2025-03-31: replaced simple moving averages with EMAs, made periods configurable).
- `ml_data_preparer.py`: Prepares data for ML models (updated 2025-03-31: added future price-based labels, added input validation, added configurable normalization method).
- `ml_data_preparer_utils.py`: Utility functions for ML data preparation (updated 2025-03-31: added configurable normalization method).
- `ml_model_trainer.py`: Trains ML models (updated 2025-03-31: replaced simple model with deep neural network, made training parameters configurable, added train/validation split, added metrics saving 2025-04-01).
- `ml_predictor.py`: Makes ML predictions (updated 2025-03-31: added input size validation, added option to return probabilities, added batch prediction support 2025-04-01).
- `model_utils.py`: Utility functions for ML models (updated 2025-03-31: added validation for PyTorch model format).
- `monetization.py`: Handles fees and monetization (updated 2025-03-31: integrated into `trade_executor_core.py`).
- `notification_manager.py`: Manages notifications (added 2025-04-01: supports email notifications, integrated into `trade_executor_core.py`).
- `ohlcv_analyzer.py`: Analyzes OHLCV data (updated 2025-03-31: added candlestick pattern detection, added input validation).
- `ohlcv_fetcher.py`: Fetches OHLCV data (updated 2025-03-31: added user_id for authentication, added as_dataframe option, added symbol validation via `symbol_handler.py`, added pagination 2025-04-01).
- `order_utils.py`: Utility functions for order management (updated 2025-03-31: added support for additional order parameters, added symbol validation via `symbol_handler.py`, added order cancellation 2025-04-01).
- `partial_close_calculator.py`: Calculates partial position closes (updated 2025-03-31: added minimum close amount check, integrated into `trade_executor_core.py`).
- `position_monitor.py`: Monitors open positions (updated 2025-03-31: added stop-loss/take-profit monitoring, integrated `trade_pool_core.py`, added symbol validation via `symbol_handler.py`, added auto-closing 2025-04-01).
- `redis_client.py`: Manages Redis connections (updated 2025-03-31: made Redis URL configurable, added automatic initialization).
- `retraining_manager.py`: Manages model retraining (updated 2025-03-30: fixed data loading issue, added error handling, added scheduled retraining 2025-04-01).
- `risk_manager.py`: Manages trade risk (updated 2025-03-31: added maximum risk check, integrated into `trade_executor_core.py`).
- `signal_blacklist.py`: Manages blacklisted symbols (updated 2025-03-31: made blacklist configurable, integrated into `bot_trading.py` and `start_trading_all.py`).
- `signal_generator_core.py`: Generates trading signals (updated 2025-03-30: made overbought/oversold thresholds configurable).
- `signal_generator_indicators.py`: Calculates indicators for signals (updated 2025-03-30: added GPU support with cupy, added CPU fallback).
- `strategies.py`: Manages trading strategies (updated 2025-03-30: improved strategy recommendation with moving averages, made periods configurable).
- `symbol_data_fetcher.py`: Fetches symbol data (updated 2025-03-31: added dynamic symbol data fetching, added symbol validation via `symbol_handler.py`, added caching 2025-04-01).
- `symbol_handler.py`: Validates symbols (updated 2025-04-01: replaced static validation with dynamic check via `exchange_factory.py`, added symbol activity check, added volume check 2025-04-01).
- `symbol_trade_processor.py`: Processes trades for a symbol (updated 2025-04-01: added trade processing with loss threshold, integrated `trade_pool_core.py` and `trade_executor_core.py`, added symbol validation via `symbol_handler.py`).
- `test_symbols.py`: Provides test symbols (updated 2025-04-01: replaced static list with dynamic fetching from exchange, added symbol validation via `symbol_handler.py`, added volume filtering 2025-04-01).
- `token_analyzer.py`: Analyzes token market data (updated 2025-04-01: added volume and volatility analysis, integrated `exchange_utils.py` and `ohlcv_fetcher.py`, added symbol validation via `symbol_handler.py`).
- `trade_pool_core.py`: Manages trade pool (updated 2025-04-01: added symbol validation via `symbol_handler.py`, replaced direct `fetch_ticker` with `exchange_utils.py`, added `clear_trades` method, added auto-cleanup of outdated trades 2025-04-01).
- `trade_pool_manager.py`: Manages trade pool operations (updated 2025-04-01: added trade pool management with cleanup of outdated trades, integrated `trade_pool_core.py`, added input validation, added scheduled cleanup 2025-04-01).

## Entry Point
- `main.py`: Main entry point for the system (added 2025-04-01: launches trading, trade pool cleanup, position monitoring, and model retraining).

## Roadmap
- Add API key validation in trading modules [Done: 2025-03-31].
- Integrate ML predictions into trading signals [Done: 2025-03-31].
- Add test mode for real trading [Done: 2025-03-30].
- Remove placeholders in core modules [Done: 2025-03-30].
- Improve logging across all modules [Done: 2025-03-30].
- Add input validation in all modules [Done: 2025-03-31].
- Integrate risk management (`limits.py`, `risk_manager.py`) [Done: 2025-03-31].
- Add support for partial position closing [Done: 2025-03-31].
- Add dynamic symbol validation [Done: 2025-04-01].
- Add trade pool management with cleanup [Done: 2025-04-01].
- Add historical data fetching for backtesting [Done: 2025-04-01].
- Add notification system [Done: 2025-04-01].
- Add Telegram bot integration [Pending].

## Dependencies
- `trade_executor_core.py` -> `exchange_factory.py`, `order_utils.py`, `trade_executor_signals.py`, `limits.py`, `trade_pool_core.py`, `exit_points_calculator.py`, `monetization.py`, `partial_close_calculator.py`, `risk_manager.py`, `balance_manager.py`, `symbol_handler.py`, `notification_manager.py`
- `trade_executor_signals.py` -> `signal_generator_indicators.py`, `ohlcv_fetcher.py`, `local_model_api.py`, `indicators.py`
- `bot_trading.py` -> `trade_executor_core.py`, `trade_executor_signals.py`, `bot_user_data.py`, `limits.py`, `balance_manager.py`, `exchange_factory.py`, `trade_pool_core.py`, `deposit_calculator.py`, `signal_blacklist.py`, `symbol_handler.py`
- `start_trading_all.py` -> `bot_trading.py`, `bot_user_data.py`, `limits.py`, `trade_pool_core.py`, `exchange_factory.py`, `balance_manager.py`, `deposit_calculator.py`, `signal_blacklist.py`, `symbol_handler.py`
- `main.py` -> `start_trading_all.py`, `bot_user_data.py`, `test_symbols.py`, `trade_pool_manager.py`, `position_monitor.py`, `retraining_manager.py`, `ml_model_trainer.py`
- `api_server.py` -> None
- `backtest_cycle.py` -> `bot_trading.py`, `historical_data_fetcher.py`
- `bot_user_data.py` -> `redis_client.py`
- `cache_utils.py` -> `redis_client.py`
- `check_all_trades.py` -> `config_keys.py`, `exchange_factory.py`, `trade_pool_core.py`, `symbol_handler.py`
- `data_utils.py` -> None
- `deposit_calculator.py` -> None
- `deposit_manager.py` -> `config_keys.py`, `exchange_factory.py`, `balance_manager.py`, `symbol_handler.py`
- `exchange_factory.py` -> `logging_setup.py`, `config_keys.py`
- `exchange_utils.py` -> `symbol_handler.py`
- `exit_points_calculator.py` -> None
- `features.py` -> None
- `historical_data_fetcher.py` -> `exchange_factory.py`, `symbol_handler.py`
- `indicators.py` -> None
- `limits.py` -> `config_keys.py`
- `market_rentgen_core.py` -> `exchange_utils.py`, `ohlcv_fetcher.py`, `symbol_handler.py`
- `market_trend_checker.py` -> None
- `ml_data_preparer.py` -> `features.py`, `ml_data_preparer_utils.py`
- `ml_data_preparer_utils.py` -> None
- `ml_model_trainer.py` -> None
- `ml_predictor.py` -> `ml_model_trainer.py`
- `model_utils.py` -> None
- `monetization.py` -> None
- `notification_manager.py` -> None
- `ohlcv_analyzer.py` -> None
- `ohlcv_fetcher.py` -> `exchange_factory.py`, `symbol_handler.py`
- `order_utils.py` -> `symbol_handler.py`
- `partial_close_calculator.py` -> `config_keys.py`
- `position_monitor.py` -> `exchange_factory.py`, `trade_pool_core.py`, `trade_executor_core.py`, `symbol_handler.py`
- `redis_client.py` -> None
- `retraining_manager.py` -> `ml_model_trainer.py`
- `risk_manager.py` -> None
- `signal_blacklist.py` -> None
- `signal_generator_core.py` -> None
- `signal_generator_indicators.py` -> None
- `strategies.py` -> None
- `symbol_data_fetcher.py` -> `exchange_factory.py`, `symbol_handler.py`, `cache_utils.py`
- `symbol_handler.py` -> `exchange_factory.py`
- `symbol_trade_processor.py` -> `exchange_factory.py`, `trade_pool_core.py`, `trade_executor_core.py`, `symbol_handler.py`
- `test_symbols.py` -> `exchange_factory.py`, `symbol_handler.py`
- `token_analyzer.py` -> `exchange_factory.py`, `exchange_utils.py`, `ohlcv_fetcher.py`, `symbol_handler.py`
- `trade_pool_core.py` -> `redis_client.py`, `cache_utils.py`, `exchange_utils.py`, `symbol_handler.py`
- `trade_pool_manager.py` -> `trade_pool_core.py`
