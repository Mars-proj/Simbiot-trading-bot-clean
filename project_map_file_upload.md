# Project Map: File Upload for Analysis

## Overview
This file tracks the steps to upload all Python modules from the trading bot project to Grok for analysis, ensuring that the process is reliable and efficient.

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

## Steps to Upload Files for Analysis
### Objective
Upload all 100 Python modules from `/root/trading_bot` to Grok in a reliable JSON format, splitting the process into parts to avoid system overload, and enable Grok to analyze the modules for optimization and consistency.

### Steps
1. **Install Required Tools**:
   - Installed `jq` for JSON processing.
   - Command: `apt install -y jq`
   - Status: Completed (jq-1.6 installed).

2. **Clean Up Previous Files**:
   - Removed old `project_state.json` and its parts.
   - Removed temporary file lists.
   - Commands:
     ```bash
     rm -f /root/trading_bot/project_state.json
     rm -f /root/trading_bot/project_state_part*.json
     rm -f /root/trading_bot/file_list.txt
     rm -f /root/trading_bot/file_list_part_*
