from typing import Any, List, Tuple

import psycopg2

from csgo_clips_autotrim.experiment_utils.config import DBConfig

class Database:
    def __init__(self, config: DBConfig):
        self._conn = psycopg2.connect(
            database=config.name,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
        )
        self._conn.autocommit = False
        self._cursor = self._conn.cursor()
    
    def execute_query(self, query, params=None):
        self._cursor.execute(query, params)
    
    def fetch_all(self) -> List[Tuple[Any]]:
        return self._cursor.fetchall()

    def fetch_one(self) -> Tuple[Any]:
        return self._cursor.fetchone()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._cursor.close()
        self._conn.close()
