from fastapi import FastAPI, HTTPException
from transformers import pipeline
import torch
import logging
import os
from trade_pool_transfer import start_trade_transfer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Check if model is already downloaded
model_path = os.path.expanduser("~/.cache/huggingface/hub/models--gpt2/snapshots")
if os.path.exists(model_path):
    logger.info(f"Model 'gpt2' found locally at {model_path}")
    model_location = "gpt2"
else:
    logger.info("Model 'gpt2' not found locally, will attempt to download")
    model_location = "gpt2"

try:
    # Check if GPU is available
    device = 0 if torch.cuda.is_available() else -1
    logger.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")
    # Load the model
    logger.info(f"Attempting to load model from {model_location}")
    model = pipeline("text-generation", model=model_location, device=device)
    logger.info("Model 'gpt2' loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    model = None

@app.post("/generate")
async def generate_text(prompt: str):
    if model is None:
        logger.error("Model not loaded, cannot generate text")
        raise HTTPException(status_code=500, detail="Model not loaded")
    try:
        logger.info(f"Generating text for prompt: {prompt}")
        result = model(prompt, max_length=50, num_return_sequences=1)
        generated_text = result[0]["generated_text"]
        logger.info(f"Generated text: {generated_text}")
        return {"text": generated_text}
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Событие при запуске приложения"""
    logger.info("Starting trade transfer task")
    start_trade_transfer()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
