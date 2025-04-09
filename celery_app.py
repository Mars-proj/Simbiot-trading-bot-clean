# celery_app.py
from celery import Celery

app = Celery('celery_app', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'

@app.task
def process_user_task(user, credentials, since, limit, timeframe, symbol_batch):
    # Добавляем timeframe в список аргументов
    from core import process_user
    import asyncio
    asyncio.run(process_user(user, credentials, since, limit, timeframe, symbol_batch))
