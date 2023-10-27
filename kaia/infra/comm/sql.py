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
from sqlalchemy import create_engine


class SqliteMemoryConnection(ISqlConnection, IComm):
    def __init__(self, check_same_thread = False):
        self.connection = sqlite3.connect(database=':memory:', check_same_thread = check_same_thread)

    def open(self):
        return self.connection

    def close(self, db):
        pass

    def messenger(self, table_name = None) -> SqlMessenger:
        return SqlMessenger(self, table_name)

    def storage(self, table_name = None) -> SqlStorage:
        return SqlStorage(self, table_name)

    def engine(self):
        return create_engine('sqlite://', echo=True)


class SqlFileConnection(ISqlConnection, IComm):
    def __init__(self, database):
        self.database = database

    def open(self):
        return sqlite3.connect(database=self.database)

    def close(self, db):
        if db is not None:
            db.close()

    def messenger(self, table_name = None) -> SqlMessenger:
        return SqlMessenger(self, table_name)

    def storage(self, table_name = None) -> SqlStorage:
        return SqlStorage(self, table_name)

    def engine(self):
        return create_engine('sqlite:///'+str(self.database))


class Sql:
    @staticmethod
    def memory():
        return SqliteMemoryConnection(check_same_thread=False)

    @staticmethod
    def file(location=None, reset_if_existed=False):
        if location is None:
            location = Loc.temp_folder / 'misc_sql_databases' / str(uuid4())
        else:
            if reset_if_existed and os.path.isfile(location):
                os.remove(location)

        os.makedirs(Path(location).parent, exist_ok=True)
        return SqlFileConnection(location)


    @staticmethod
    def file_timestamp(folder: Path):
        os.makedirs(folder, exist_ok=True)
        path = folder/datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        return SqlFileConnection(path)

    @staticmethod
    def test_file(name: str):
        path = Loc.temp_folder/'tests'/name
        os.makedirs(path.parent, exist_ok=True)
        return Sql.file(path, True)


