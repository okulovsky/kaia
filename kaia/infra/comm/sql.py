from typing import *
from .i_sql_connection import ISqlConnection
from .sql_messenger import SqlMessenger
from .sql_storage import SqlStorage
from .i_comm import IComm
import sqlite3
from ..loc import Loc
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime


class SqlConnection(ISqlConnection, IComm):
    def __init__(self, name: str, memory_mode: bool, database, kwargs):
        self.name = name
        self.memory_mode = memory_mode
        self.database = database
        self.kwargs = kwargs
        self.db = None
        if self.memory_mode:
            self.db = self._connect()

    def _connect(self):
        return sqlite3.connect(database=self.database, **self.kwargs)

    def open(self):
        if self.memory_mode:
            return self.db
        else:
            return self._connect()

    def close(self, db):
        if not self.memory_mode and db is not None:
            db.close()

    def messenger(self, table_name = None) -> SqlMessenger:
        return SqlMessenger(self, table_name)

    def storage(self, table_name = None) -> SqlStorage:
        return SqlStorage(self, table_name)






class Sql:
    @staticmethod
    def memory():
        return SqlConnection('memory', True, ':memory:', dict(check_same_thread=False))

    @staticmethod
    def file(location=None, reset_if_existed=False):
        if location is None:
            location = Loc.temp_folder / 'misc_sql_databases' / str(uuid4())
        else:
            if reset_if_existed and os.path.isfile(location):
                os.remove(location)

        os.makedirs(Path(location).parent, exist_ok=True)
        return SqlConnection('file', False, location, {})


    @staticmethod
    def file_timestamp(folder: Path):
        os.makedirs(folder, exist_ok=True)
        path = folder/datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        return SqlConnection('file', False, path, {})