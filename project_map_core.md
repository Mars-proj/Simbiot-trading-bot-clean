# Project Map: Core Modules

## Overview
This file contains information about the core modules, configuration, and global objects of the trading bot project.

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

## Directory Structure
- **/root/trading_bot/**
  - Main project directory containing all Python modules, logs, and data files.

## Modules

### Core Modules
- **trading_part1.py**
  - **Purpose**: Entry point of the trading bot. Initializes loggers, global objects, validates settings, checks network connectivity, and starts the main trading cycle.
  - **Dependencies**:
    - `sys`
    - `asyncio`
    - `subprocess`
    - `logging_setup.initialize_loggers`, `logging_setup.shutdown_loggers`, `logging_setup.logger_main`
    - `config_keys.validate_api_keys`
    - `config_settings.LOGGING_SETTINGS`, `config_settings.validate_logging_settings`
    - `config_notifications.validate_notification_settings`
    - `trading_cycle.main`
    - `trade_pool_core.TradePool`
    - `global_objects`
  - **Size**: 108 lines
  - **Notes**: Optimized for network checking using `subprocess` and simplified logging. Added logging for `redis_client` initialization.

- **trading_cycle.py**
  - **Purpose**: Manages the main trading cycle, orchestrating symbol processing and trade execution.
  - **Dependencies**:
    - `asyncio`
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `symbol_handler.process_symbols`
    - `config_keys.API_KEYS`
  - **Size**: Unknown (not provided)
  - **Notes**: Needs optimization for parallel symbol processing.

- **symbol_handler.py**
  - **Purpose**: Handles symbol processing logic, coordinating with `symbol_filter.py` and trade execution.
  - **Dependencies**:
    - `asyncio`
    - `logging_setup.logger_main`
    - `utils.log_exception`
    - `symbol_filter.filter_symbols`
    - `global_objects.global_trade_pool`
  - **Size**: Unknown (not provided)
  - **Notes**: Needs optimization for parallel processing.

- **worker.py**
  - **Purpose**: Likely a worker process for background tasks (e.g., processing symbols, trades).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

### Configuration Modules
- **config_keys.py**
  - **Purpose**: Stores API keys and preferred exchanges for users, and provides validation for API keys.
  - **Dependencies**:
    - None (uses `logger_main` passed as argument)
  - **Size**: 62 lines
  - **Notes**: Created as part of `config.py` split for better modularity.

- **config_settings.py**
  - **Purpose**: Manages dynamic symbol criteria, backtesting settings, exchange connection settings, cache settings, and logging settings, with validation.
  - **Dependencies**:
    - None (uses `logger_main` passed as argument)
  - **Size**: 108 lines
  - **Notes**: Created as part of `config.py` split. Optimized `rateLimit` for 10 Gbit/s network.

- **config_notifications.py**
  - **Purpose**: Stores notification settings (Telegram, email) and provides validation.
  - **Dependencies**:
    - None (uses `logger_main` passed as argument)
  - **Size**: 37 lines
  - **Notes**: Created as part of `config.py` split.

- **config.py**
  - **Purpose**: Legacy configuration file (replaced by `config_keys.py`, `config_settings.py`, `config_notifications.py`).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Likely deprecated; consider removing after analysis.

### Global Objects
- **global_objects.py**
  - **Purpose**: Holds global instances like `global_trade_pool` and `redis_client`.
  - **Dependencies**:
    - `trade_pool_core.TradePool`
    - `redis_initializer.redis_client`
  - **Size**: 6 lines
  - **Notes**: Optimized with comments for clarity.

- **redis_initializer.py**
  - **Purpose**: Initializes the global `redis_client` instance to avoid circular imports.
  - **Dependencies**:
    - `redis_client.RedisClient`
  - **Size**: 5 lines
  - **Notes**: Removed logging to avoid initialization issues; logging moved to `trading_part1.py`.

- **state.py**
  - **Purpose**: Likely manages global state or session data for the bot.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.
