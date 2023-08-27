import asyncio
import logging
import os
import pathlib
import subprocess
import tempfile
import threading
import uuid

from typing import Optional

import pydantic

from webserver.models import Task, TaskRequest, TaskStatus

logger = logging.getLogger(__name__)

class Manager:
    def __init__(self):
        self._work_dir = pathlib.Path(tempfile.mkdtemp(prefix='autotrim-tasks-'))
        self._tasks_dir = self._work_dir / 'tasks'
        self._tasks_dir.mkdir(exist_ok=True)
        self._concurrency_limit = 1
        self._tasks = dict()
        self._lock = threading.Lock()
    
    def get_active_task_count(self):
        return len(os.listdir(self._tasks_dir))
    
    def start_task(self, task_request: TaskRequest) -> str:
        with self._lock:
            active_task_count = self.get_active_task_count() 

            if active_task_count >= self._concurrency_limit:
                raise ValueError(f'Cannot start more than {self._concurrency_limit} tasks, {active_task_count} tasks active.')
            
            task_id = uuid.uuid4().hex

            task_dir = self._tasks_dir / task_id
            task_dir.mkdir()

            task = Task(task_id=task_id, command=task_request.command, args=task_request.args, working_dir=task_dir.as_posix(), status=TaskStatus.ACCEPTED)
            task.save(self._work_dir)

            self._tasks[task_id] = asyncio.create_task(self._run_task(task))
            return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        task_file = Task.get_task_file_path(self._work_dir, task_id)

        if not task_file.exists():
            return None

        return pydantic.parse_file_as(path=task_file, type_=Task)
    
    async def _run_task(self, task: Task):
        logger.info('Started worker for task_id: %s, working dir: %s', task.task_id, task.working_dir)
        task.update_status(TaskStatus.RUNNING)
        task.save(self._work_dir)

        logger.info('Running command: %s, args: %s', task.command, task.args)

        try:
            process = await asyncio.create_subprocess_shell(
                f'{task.command} {" ".join(task.args)}',
                cwd=task.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise ValueError('Non zero exit code.')

            task.update_returncode(process.returncode)
            task.update_stderr(stderr.decode().strip())
            task.update_stdout(stdout.decode().strip())
            task.update_status(TaskStatus.SUCCESS)
            task.save(self._work_dir)
        except Exception as e:
            logger.exception('Task ID: %s, exception when running subprocess for command: %s', task.task_id, task.command)
            task.update_returncode(process.returncode)
            task.update_stderr(stderr.decode().strip())
            task.update_stdout(stdout.decode().strip())
            task.update_status(TaskStatus.FAILED)
            task.save(self._work_dir)
        finally:
            os.rmdir(task.working_dir)