import enum
import json
import os
import pathlib
from typing import List, Optional

from pydantic import BaseModel

class Result(BaseModel):
    success: bool = True
    reason: str = "OK"

class TaskRequest(BaseModel):
    command: str
    args: List[str]

    class Config:
        schema_extra = {
            'examples': [
                {
                    'command': 'ingest',
                    'args': ['--source-dir', '/data']
                }
            ]
        }

class StartTaskResponse(BaseModel):
    result: Result
    task_id: Optional[str]

    class Config:
        schema_extra = {
            'examples': [
                {
                    'result': {
                        'success': True,
                        'reason': 'OK'
                    },
                    'task_id': '01234567890abcde'
                }
            ]
        }

class TaskStatus(str, enum.Enum):
    ACCEPTED = 'ACCEPTED'
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

class Task(BaseModel):
    task_id: str
    command: str
    args: List[str]
    working_dir: str
    status: TaskStatus
    returncode: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]

    @classmethod
    def get_task_file_path(cls, working_dir: os.PathLike, task_id: str) -> pathlib.Path:
        return pathlib.Path(working_dir) / f'{task_id}.json'

    def update_status(self, status: TaskStatus):
        self.status = status

    def update_returncode(self, returncode: int):
        self.returncode = returncode

    def update_stdout(self, stdout: str):
        self.stdout = stdout

    def update_stderr(self, stderr: str):
        self.stderr = stderr

    def save(self, working_dir: os.PathLike):
        task_file = Task.get_task_file_path(working_dir=working_dir, task_id=self.task_id)
        task_file.write_text(json.dumps(dict(self)))

class GetTaskResponse(BaseModel):
    result: Result
    task: Optional[Task]