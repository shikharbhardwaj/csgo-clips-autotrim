import dataclasses
import datetime
import logging

from typing import Any, List, Tuple

from cli.database import Database

logger = logging.getLogger('__name__')


@dataclasses.dataclass
class IngestEntry:
    ingest_id: str
    path: str
    ingested_at_utc: datetime.datetime

    @classmethod
    def table_name(cls) -> str:
        return 'ingest_queue'
    
    def _get_field_names(self) -> Tuple[str]:
        return tuple(x.name for x in dataclasses.fields(self))
    
    def _get_field_values(self) -> Tuple[Any]:
        return tuple(getattr(self, name) for name in self._get_field_names())

    @staticmethod
    def search_ingest_entry(db: Database, ingest_id: str, **kwargs) -> List['IngestEntry']:
        query = f'''
        SELECT * FROM {IngestEntry.table_name()}
        WHERE ingest_id = %s
        '''
        db.execute_query(query, (ingest_id,))

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
class Result:
    ingest_id: str
    timeline_result: str
    clutch_detection_result: str
