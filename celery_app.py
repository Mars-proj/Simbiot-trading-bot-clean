# celery_app.py
import sys
import os

# Добавляем текущую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery import Celery

app = Celery('celery_app', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'

@app.task
def process_user_task(user, credentials, since, limit, timeframe, symbol_batch):
    from core import process_user
    import asyncio
    asyncio.run(process_user(user, credentials, since, limit, timeframe, symbol_batch))
