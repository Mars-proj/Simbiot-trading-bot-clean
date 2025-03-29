# Project Map: Power Enhancement for Grok

## Overview
This file tracks the steps to enhance Grok's processing capabilities by running a local AI model on the server, leveraging the Tesla T4 GPU, to offload computation and speed up analysis.

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

## Steps to Add Processing Power for Grok
### Objective
Enhance Grok's processing capabilities by running a local AI model on the server, leveraging the Tesla T4 GPU, to offload computation and speed up analysis.

### Steps
1. **Install Dependencies for Local Model**:
   - Installed `fastapi` and `uvicorn` for API server.
   - Installed `transformers` and `torch` for model loading.
   - Installed `bitsandbytes` and `accelerate` for model optimization (e.g., 8-bit quantization).
   - Command: `pip install fastapi uvicorn transformers torch bitsandbytes accelerate`

2. **Create `local_model_api.py`**:
   - Created a FastAPI application to serve a local AI model.
   - Initially tried `mistralai/Mixtral-8x7B-Instruct-v0.1`, but failed due to memory constraints (Tesla T4 has 16 GB).
   - Switched to `distilgpt2`, but encountered loading issues.
   - Switched to `gpt2` with detailed logging for debugging.
   - Added local model path checking and enhanced logging in Update 49.
   - File: `local_model_api.py`

3. **Launch Local Model API**:
   - Launched using `uvicorn` with full path to ensure virtual environment usage.
   - Added `--app-dir /root/trading_bot` to fix module import issues.
   - Command: `nohup /root/trading_bot/venv/bin/uvicorn local_model_api:app --app-dir /root/trading_bot --host 0.0.0.0 --port 8000 > /root/trading_bot/local_model_api.log 2>&1 &`
   - Log file: `local_model_api.log`
   - Status: Model `gpt2` downloaded successfully, but CUDA driver (version 11.8) is too old; running on CPU. Installed PyTorch 2.0.1+cu118 for compatibility.

4. **Debug Model Loading**:
   - Checked network access to Hugging Face: `curl -I https://huggingface.co` (successful, HTTP/2 200).
   - Confirmed `gpt2` model downloaded: `python3 -c "from transformers import pipeline; pipeline('text-generation', model='gpt2')"` (successful).
   - CUDA driver issue: Version 11.8 too old for current PyTorch; installed PyTorch 2.0.1+cu118 to match CUDA 11.8.
   - Ran `uvicorn` without `nohup` to capture full output for debugging.

5. **Integrate with Grok**:
   - Once the API is running, Grok can send requests to `http://45.140.147.187:8000/generate` with a prompt to get generated text.
   - Example request: `curl -X POST -H "Content-Type: application/json" -d '{"prompt": "Analyze trading data"}' http://45.140.147.187:8000/generate`

### Challenges
- **Model Size**: Large models like `Mixtral-8x7B` exceed Tesla T4 memory (16 GB); switched to smaller models (`distilgpt2`, then `gpt2`).
- **Module Import**: `uvicorn` failed to find `local_model_api` due to incorrect working directory; fixed with `--app-dir`.
- **CUDA Driver**: Version 11.8 too old for current PyTorch; installed PyTorch 2.0.1+cu118, but still running on CPU.
- **Model Loading**: `local_model_api.py` process starts but does not complete model loading; needs further debugging.

### Next Steps for Power Enhancement
- Debug `local_model_api.py` model loading issue (check PyTorch compatibility, memory usage, `transformers` configuration).
- If CPU usage is too slow, consider updating NVIDIA driver to support newer PyTorch versions for GPU usage.
- Test API endpoint with a simple request once running.
- Integrate API calls into Grok's workflow for faster analysis.
