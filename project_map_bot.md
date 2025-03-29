# Project Map: Bot Commands

## Overview
This file contains information about the bot command modules of the trading bot project.

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

### Bot Commands
- **bot_commands_core.py**
  - **Purpose**: Core bot commands (`/start`, `/register`, `/lang_ru`, `/lang_en`, `/language`).
  - **Dependencies**:
    - `asyncio`
    - `ccxt.async_support`
    - `telegram.Update`
    - `telegram.ext.ContextTypes`
    - `logging_setup.logger_main`
    - `logging_setup.logger_exceptions`
    - `bot_translations.get_translation`
    - `bot_user_data.user_data`, `bot_user_data.save_user_data`, `bot_user_data.check_duplicate_keys`, `bot_user_data.add_user_to_config`
    - `bot_trading.start_trading`
    - `importlib`
  - **Size**: 178 lines
  - **Notes**: Part of `bot_commands.py` split for modularity. Updated on 2025-03-26 to replace `config` with `config_keys` and `utils.log_exception` with `logging_setup.logger_exceptions`.
- **bot_commands_balance.py**
  - **Purpose**: Commands for balance and PNL (`/balance`, `/pnl`).
  - **Dependencies**:
    - `asyncio`
    - `ccxt.async_support`
    - `telegram.Update`
    - `telegram.ext.ContextTypes`
    - `logging_setup.logger_main`
    - `logging_setup.logger_exceptions`
    - `bot_translations.get_translation`
    - `bot_user_data.user_data`
    - `trade_pool_queries.get_all_trades`
    - `config_keys.API_KEYS`
    - `time`
    - `async_exchange_fetcher.async_exchange_fetcher`
    - `bot_commands_core.save_config`
  - **Size**: 178 lines
  - **Notes**: Part of `bot_commands.py` split, can be optimized for parallel balance fetching. Updated on 2025-03-26 to replace `config` with `config_keys` and `utils.log_exception` with `logging_setup.logger_exceptions`.
- **bot_translations.py**
  - **Purpose**: Manages translations for multi-language support.
  - **Dependencies**:
    - None
  - **Size**: 149 lines
  - **Notes**: Can be optimized by loading translations from a JSON file.
- **bot_user_data.py**
  - **Purpose**: Manages user data (language, chat_id) and API key registration.
  - **Dependencies**:
    - `json`
    - `importlib`
    - `config_keys.API_KEYS`, `config_keys.PREFERRED_EXCHANGES`
  - **Size**: 90 lines
  - **Notes**: Can be optimized by using a database for user data. Updated on 2025-03-26 to replace `config` with `config_keys` and update logic for writing to `config_keys.py`.
- **check_balance.py**
  - **Purpose**: Likely a script to check user balances (possibly for all users).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies. Identified as potential "dead" code (functionality moved to `bot_commands_balance.py`).
- **check_balance_user1.py**
  - **Purpose**: Likely a script to check balance for a specific user (USER1).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may be redundant with `check_balance.py`. Identified as potential "dead" code (functionality moved to `bot_commands_balance.py`).
- **notification_utils.py**
  - **Purpose**: Utility functions for sending notifications (e.g., via Telegram, email).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.
- **telegram_bot.py**
  - **Purpose**: Main Telegram bot logic (possibly replaced by `bot_commands_*.py`).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may be deprecated. Identified as "dead" code (functionality moved to `bot_commands_*.py`).
- **user_exchange_setup.py**
  - **Purpose**: Sets up exchange connections for users (e.g., API keys).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

## Updates
- **2025-03-26**: Removed `bot_commands_status.py` as it was identified as "dead" code (functionality moved to `bot_commands_core.py` and `bot_commands_balance.py`).
- **2025-03-26**: Updated `bot_user_data.py` to replace `config` with `config_keys` and update logic for writing to `config_keys.py`.
- **2025-03-26**: Updated `bot_commands_core.py` to replace `config` with `config_keys` and `utils.log_exception` with `logging_setup.logger_exceptions`.
- **2025-03-26**: Updated `bot_commands_balance.py` to replace `config` with `config_keys` and `utils.log_exception` with `logging_setup.logger_exceptions`.
