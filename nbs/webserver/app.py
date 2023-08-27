import logging
import os
import traceback

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from webserver.models import GetTaskResponse, Result, StartTaskResponse, TaskRequest
from webserver import tasks

app = FastAPI()

log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(format='[%(levelname)8s] %(asctime)s %(filename)16s:L%(lineno)-3d %(funcName)16s() : %(message)s', level=log_level)
logger = logging.getLogger(__name__)

task_manager = tasks.Manager()

@app.get('/')
async def root():
    return {'app': 'autotrim', 'version': '0.1.0'}

@app.post('/task')
async def start_task(task_request: TaskRequest) -> StartTaskResponse:
    try:
        task_id = task_manager.start_task(task_request)
        return StartTaskResponse(result=Result(), task_id=task_id)
    except:
        logger.exception('Failed to start task')
        return StartTaskResponse(result=Result(success=False, reason=traceback.format_exc()))

@app.get('/task')
async def get_task(task_id: str) -> GetTaskResponse:
    try:
        task = task_manager.get_task(task_id)
        logger.info('Got task with id %s: %s', task_id, task)
        if task is None:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                                content=GetTaskResponse(result=Result(success=False, reason=f'Task with ID: {task_id} not found')).dict())
        return GetTaskResponse(result=Result(), task=task)
    except:
        logger.exception('Failed to get task')
        return GetTaskResponse(result=Result(success=False, reason=traceback.format_exc()))