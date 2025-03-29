import logging
import sys
import os
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import subprocess
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting api_server.py")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")

app = FastAPI()

# Токен для аутентификации (в реальной системе это должен быть секретный ключ)
API_TOKEN = "grok_access_token_2025"

def verify_token(authorization: str = Header(...)):
    """Проверяет токен в заголовке Authorization"""
    if authorization != f"Bearer {API_TOKEN}":
        logger.error(f"Invalid token: {authorization}")
        raise HTTPException(status_code=401, detail="Invalid token")
    logger.info("Token verified successfully")

class CommandRequest(BaseModel):
    command: str
    working_dir: Optional[str] = "/root/trading_bot"

class WriteFileRequest(BaseModel):
    filename: str
    content: str

@app.on_event("startup")
async def startup_event():
    logger.info("Starting API server...")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url} from {request.client.host}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response

@app.post("/execute")
def execute_command(request: CommandRequest, authorization: str = Header(...)):
    verify_token(authorization)
    try:
        logger.info(f"Received command: {request.command}, working_dir: {request.working_dir}")
        # Устанавливаем рабочую директорию
        os.chdir(request.working_dir)
        # Выполняем команду
        result = subprocess.run(request.command, shell=True, capture_output=True, text=True)
        logger.info(f"Command executed with return code: {result.returncode}")
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/write_file")
def write_file(request: WriteFileRequest, authorization: str = Header(...)):
    verify_token(authorization)
    try:
        filename = request.filename
        content = request.content
        logger.info(f"Attempting to write file: {filename}")
        # Проверяем, существует ли директория
        directory = os.path.dirname(filename)
        logger.info(f"Directory path: {directory}")
        if directory and not os.path.exists(directory):
            logger.info(f"Directory {directory} does not exist, creating it")
            os.makedirs(directory, exist_ok=True)
        else:
            logger.info(f"Directory {directory} exists")
        # Проверяем права доступа к директории
        if not os.access(directory, os.W_OK):
            logger.error(f"No write permission for directory {directory}")
            raise HTTPException(status_code=500, detail=f"No write permission for directory {directory}")
        logger.info(f"Directory {directory} is writable")
        # Проверяем, существует ли файл
        if os.path.exists(filename):
            logger.info(f"File {filename} exists, checking permissions")
            if not os.access(filename, os.W_OK):
                logger.error(f"No write permission for file {filename}")
                raise HTTPException(status_code=500, detail=f"No write permission for file {filename}")
            logger.info(f"File {filename} is writable")
        else:
            logger.info(f"File {filename} does not exist, will create it")
        # Записываем файл
        logger.info(f"Opening file {filename} for writing")
        with open(filename, "w") as f:
            logger.info(f"Writing content to {filename}")
            f.write(content)
            logger.info(f"Content written to {filename}")
        logger.info(f"File {filename} written successfully")
        # Проверяем, что файл действительно создан
        if not os.path.exists(filename):
            logger.error(f"File {filename} was not created after writing")
            raise HTTPException(status_code=500, detail=f"File {filename} was not created after writing")
        logger.info(f"File {filename} exists after writing")
        return {"message": f"File {filename} written successfully"}
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read_file")
def read_file(filename: str, authorization: str = Header(...)):
    verify_token(authorization)
    try:
        logger.info(f"Reading file: {filename}")
        # Проверяем права доступа
        if not os.path.exists(filename):
            logger.error(f"File {filename} does not exist")
            raise HTTPException(status_code=404, detail=f"File {filename} does not exist")
        if not os.access(filename, os.R_OK):
            logger.error(f"No read permission for file {filename}")
            raise HTTPException(status_code=500, detail=f"No read permission for file {filename}")
        with open(filename, "r") as f:
            content = f.read()
        logger.info(f"File {filename} read successfully")
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
