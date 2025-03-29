# Project Map: Trade Pool

## Overview
This file contains information about the trade pool modules of the trading bot project.

## System Configuration and Resources
- **CPUs**: 2x Intel Xeon E5-2697A v4 (32 cores, 64 threads)
  - Used for parallel processing in `symbol_filter.py` and `bot_trading.py` with `ThreadPoolExecutor`.
- **RAM**: 384 GB DDR4
  - Allocated 300 GB for Redis caching (`maxmemory 300gb` in Redis config).
- **Storage**:
  - 2x 480 GB SSD: Used for OS and logs.
  - 1x 4 TB NVMe: Used for historical data storage.
- **Network**: 10 Gbit/s
  - Optimized `EXCHANGE_CONNECTION_SETTINGS.rateLimit` to 500 ms.
- **GPU**: NVIDIA Tesla T4 (16 GB GDDR6, 2560 CUDA cores, 8.1 TFLOPS FP32)
  - Used in `signal_generator_indicators.py` with `cupy` for indicator calculations.
  - Attempted to use in `local_model_api.py` for running local AI model (GPT-2), but CUDA driver (version 11.8) is too old; currently running on CPU.
- **IP and Location**: 45.140.147.187 (Netherlands, nl-arenda.10)

## Modules

### Trade Pool
- **trade_pool_core.py**
  - **Purpose**: Core trade pool logic for adding and updating trades.
  - **Dependencies**:
    - `redis.asyncio`
    - `uuid`
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `trade_pool_redis.add_trade_to_redis`, `trade_pool_redis.update_trade_pnl_in_redis`
    - `trade_pool_file.add_trade_to_files`, `trade_pool_file.update_trade_pnl_in_files`
    - `user_trade_cache.UserTradeCache`
    - `config_settings.LOGGING_SETTINGS`
  - **Size**: 108 lines
  - **Notes**: Part of `trade_pool.py` split for modularity.

- **trade_pool_queries.py**
  - **Purpose**: Handles trade pool queries (get trades, summaries, etc.).
  - **Dependencies**:
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `trade_pool_redis.get_all_trades_from_redis`, `trade_pool_redis.get_recent_trades_from_redis`
    - `trade_pool_tokens.update_available_tokens`, `trade_pool_tokens.get_available_tokens`
    - `redis_initializer.redis_client`
  - **Size**: 108 lines
  - **Notes**: Part of `trade_pool.py` split, optimized with simplified logging and `redis_client` checks.

- **trade_pool_redis.py**
  - **Purpose**: Manages trade storage and updates in Redis.
  - **Dependencies**:
    - `redis.asyncio`
    - `uuid`
    - `asyncio`
    - `logging_setup.logger_main`, `logging_setup.logger_trade_pool`
    - `utils.log_exception`
    - `json_handler.dumps`, `json_handler.loads`
  - **Size**: 108 lines
  - **Notes**: Can be optimized for batch operations.

- **trade_pool_file.py**
  - **Purpose**: Manages trade storage and updates in files (`trade_pool.log`, `trades.json`).
  - **Dependencies**:
    - `json`
    - `logging_setup.logger_main`, `logging_setup.logger_trade_pool`
    - `utils.log_exception`
    - `json_handler.dumps`
  - **Size**: 62 lines
  - **Notes**: Can be optimized for asynchronous file operations.

- **trade_pool_global.py**
  - **Purpose**: Likely manages global trade pool state or configuration.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `trade_pool_core.py`.

- **trade_pool_tokens.py**
  - **Purpose**: Manages available tokens for users in Redis.
  - **Dependencies**:
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `json_handler.dumps`, `json_handler.loads`
    - `redis_initializer.redis_client`
  - **Size**: 52 lines
  - **Notes**: Optimized with simplified logging and `redis_client` checks.

- **user_trade_cache.py**
  - **Purpose**: Caches user trades and summaries in Redis.
  - **Dependencies**:
    - `asyncio`
    - `redis_initializer.redis_client`
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `json_handler.dumps`, `json_handler.loads`
  - **Size**: 108 lines
  - **Notes**: Optimized with simplified logging and `redis_client` checks.

- **check_all_trades.py**
  - **Purpose**: Checks all trades in the pool (e.g., for consistency, errors).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **check_trades.py**
  - **Purpose**: Likely a script to check specific trades (possibly for a user).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `check_all_trades.py`.
