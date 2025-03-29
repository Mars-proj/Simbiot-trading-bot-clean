# Project Map: Utilities

## Overview
This file contains information about the utility modules of the trading bot project.

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

### Utilities
- **async_balance_fetcher.py**
  - **Purpose**: Asynchronously fetches user balances.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `balance_manager.py`.

- **async_exchange_fetcher.py**
  - **Purpose**: Provides asynchronous methods for fetching exchange data (markets, balance, tickers, OHLCV).
  - **Dependencies**:
    - `ccxt.async_support`
    - `asyncio`
    - `logging_setup.logger_main`
    - `utils.log_exception`
  - **Size**: 108 lines
  - **Notes**: Can be optimized for parallel fetching using `ThreadPoolExecutor`.

- **async_exchange_manager.py**
  - **Purpose**: Manages exchange connections asynchronously.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **async_ohlcv_fetcher.py**
  - **Purpose**: Asynchronously fetches OHLCV data for symbols.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `async_exchange_fetcher.py`.

- **async_order_fetcher.py**
  - **Purpose**: Asynchronously fetches order data from exchanges.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **async_ticker_fetcher.py**
  - **Purpose**: Asynchronously fetches ticker data for symbols.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `async_exchange_fetcher.py`.

- **async_utils.py**
  - **Purpose**: Utility functions for asynchronous operations.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **balance_manager.py**
  - **Purpose**: Manages user balances with caching and suspension logic.
  - **Dependencies**:
    - `ccxt.async_support`
    - `asyncio`
    - `time`
    - `logging_setup.logger_main`
    - `utils.log_exception`
  - **Size**: 109 lines
  - **Notes**: Can be optimized for parallel balance fetching.

- **balance_utils.py**
  - **Purpose**: Utilities for calculating total balance in USDT.
  - **Dependencies**:
    - `logging_setup.logger_main`, `logging_setup.logger_debug`
    - `utils.log_exception`
    - `asyncio`
    - `time`
  - **Size**: 65 lines
  - **Notes**: Can be optimized with GPU acceleration for price calculations.

- **cache_utils.py**
  - **Purpose**: Manages caching in Redis with cleanup and serialization utilities.
  - **Dependencies**:
    - `asyncio`
    - `json`
    - `time`
    - `redis_initializer.redis_client`
    - `logging_setup.logger_main`
    - `utils.log_exception`
  - **Size**: 108 lines
  - **Notes**: Optimized with simplified logging and `redis_client` checks.

- **data_fetcher.py**
  - **Purpose**: Fetches data from external sources (e.g., exchanges, APIs).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **data_utils.py**
  - **Purpose**: Utility functions for data processing.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **exchange_factory.py**
  - **Purpose**: Factory for creating exchange instances (e.g., CCXT).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **exchange_setup.py**
  - **Purpose**: Sets up exchange connections (e.g., API keys, rate limits).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **exchange_utils.py**
  - **Purpose**: Utility functions for exchange operations.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **json_handler.py**
  - **Purpose**: Provides JSON serialization/deserialization with custom handling for non-serializable types.
  - **Dependencies**:
    - `json`
    - `pandas`
    - `numpy`
  - **Size**: 37 lines
  - **Notes**: Can be optimized by adding logging for errors.

- **logging_setup.py**
  - **Purpose**: Sets up logging for the entire project.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **market_data_fetcher.py**
  - **Purpose**: Fetches market data (e.g., prices, volumes).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `async_exchange_fetcher.py`.

- **ohlcv_analyzer.py**
  - **Purpose**: Analyzes OHLCV data for patterns or trends.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **ohlcv_fetcher.py**
  - **Purpose**: Fetches OHLCV data (possibly synchronous version).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may overlap with `async_ohlcv_fetcher.py`.

- **order_utils.py**
  - **Purpose**: Utility functions for order management.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.

- **redis_client.py**
  - **Purpose**: Custom Redis client with JSON serialization support.
  - **Dependencies**:
    - `redis.asyncio`
    - `json`
  - **Size**: Unknown (not provided)
  - **Notes**: Can be optimized for connection pooling.

- **utils.py**
  - **Purpose**: General utility functions (e.g., logging, error handling).
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose; may contain deprecated code.

- **websocket_manager.py**
  - **Purpose**: Manages WebSocket connections for real-time data.
  - **Dependencies**: Unknown (to be analyzed)
  - **Size**: Unknown (to be analyzed)
  - **Notes**: Needs analysis to confirm purpose and dependencies.
