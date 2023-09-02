import abc
import dataclasses
import datetime
import logging

from typing import Any, Dict, List, Optional, Tuple

from cli.database import Database
from webserver.models import TaskStatus

logger = logging.getLogger('__name__')


@dataclasses.dataclass
class DBModel(abc.ABC):
    @classmethod
    def table_name(cls) -> str:
        raise NotImplementedError()

    def _get_field_names(self) -> Tuple[str]:
        return tuple(x.name for x in dataclasses.fields(self))
    
    def _get_field_values(self) -> Tuple[Any]:
        return tuple(getattr(self, name) for name in self._get_field_names())

@dataclasses.dataclass
class IngestEntry(DBModel):
    ingest_id: str
    path: str
    ingested_at_utc: datetime.datetime
    status: TaskStatus

    @classmethod
    def table_name(cls) -> str:
        return 'ingest_queue'
    
    def try_progress_status(self):
        task_list = list(TaskStatus)
        current_status_idx = task_list.index(self.status)
        next_status_idx = current_status_idx + 1

        if len(task_list) + 1 == next_status_idx:
            raise ValueError('Cannot progress from terminal status.')
        
        self.status = task_list[next_status_idx]

    @staticmethod
    def search_ingest_entry(db: Database, ingest_id: Optional[str] = None, status: Optional[Tuple] = None, limit: int = 10, offset: int = 0, **kwargs) -> List['IngestEntry']:
        query = f'''
        SELECT * FROM {IngestEntry.table_name()}
        WHERE 1 = 1 
        '''
        args = tuple()

        if ingest_id is not None:
            query += ' AND ingest_id = %s'
            args = args + (ingest_id,)
        
        if status is not None:
            query += ' AND status in %s'
            args = args + (status,)

        query += f''' ORDER BY ingested_at_utc LIMIT {limit} OFFSET {offset}'''
        db.execute_query(query, args)

        results = [IngestEntry(*row) for row in db.fetch_all()]
        return results
    
    def save(self, db: Database):
        field_names = self._get_field_names()
        field_values = self._get_field_values()

        num_values = len(field_values)
        placeholders = ['%s'] * num_values
        placeholder_str = ', '.join(placeholders)

        set_clause = ', '.join([f'{name} = EXCLUDED.{name}' for name in field_names])

        query = f'''
        INSERT INTO {IngestEntry.table_name()}
        VALUES ({placeholder_str})
        ON CONFLICT (ingest_id)
        DO UPDATE SET 
            {set_clause}
        '''
        try:
            db.execute_query(query, self._get_field_values())
            db.commit()
        except:
            logger.exception('Failed to save ingest entry.')
            db.rollback()


@dataclasses.dataclass
class ResultEntry(DBModel):
    ingest_id: str
    timeline: Dict
    clutch_detection_result: Dict

    @classmethod
    def table_name(cls) -> str:
        return 'result'
    
    def save(self, db: Database):
        field_names = self._get_field_names()
        field_values = self._get_field_values()

        num_values = len(field_values)
        placeholders = ['%s'] * num_values
        placeholder_str = ', '.join(placeholders)

        set_clause = ', '.join([f'{name} = EXCLUDED.{name}' for name in field_names])

        query = f'''
        INSERT INTO {ResultEntry.table_name()}
        VALUES ({placeholder_str})
        ON CONFLICT (ingest_id)
        DO UPDATE SET 
            {set_clause}
        '''
        try:
            db.execute_query(query, self._get_field_values())
            db.commit()
        except:
            logger.exception('Failed to save result entry.')
            db.rollback()
            raise