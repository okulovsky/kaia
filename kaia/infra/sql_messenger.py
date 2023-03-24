from typing import *
import json
from datetime import datetime
from uuid import uuid4
import sqlite3
import os
from functools import partial

class Message:
    def __init__(self,
                 id: str,
                 type: str,
                 payload: Any,
                 date_posted: Optional[datetime],
                 open: bool,
                 result: Any
                 ):
        self.id = id
        self.type = type
        self.payload = payload
        self.date_posted = date_posted
        self.open = open
        self.result = result


class SearchOptions:
    def __init__(self,
                 id: Optional[str] = None,
                 type: Optional[str] = None,
                 open: Optional[bool] = None
                 ):
        self.id = id
        self.type = type
        self.open = open



class IMessenger:
    def add(self, type: str, payload: Any) -> str:
        raise NotImplementedError()

    def read(self, options: Optional[SearchOptions] = None) -> List[Message]:
        raise NotImplementedError()

    def close(self, id: str, payload: Any):
        raise NotImplementedError()

    def query(self, id: Optional[str] = None, type: Optional[str] = None, open: Optional[bool] = None):
        return self.read(SearchOptions(id=id, type=type, open=open))

    def read_all_and_confirm(self, command_type):
        tasks = self.read(SearchOptions(type=command_type, open=True))
        for t in tasks:
            self.close(t.id, None)
        return tasks



import threading

lock = threading.Lock()

class SqlMessenger(IMessenger):
    def __init__(self, location: Optional[str] = None):
        if location is None:
            self.kwargs = dict(database = ':memory:', check_same_thread = False)
            self.db_ = sqlite3.connect(**self.kwargs)
        else:
            if os.path.exists(location):
                os.remove(location)
            self.kwargs = dict(database = location)
            self.db_ = None
        self._perform(self._initialize)


    def _perform(self, method):
        db = None
        cursor = None
        lock.acquire(True)
        try:
            if self.db_ is not None:
                db = self.db_
            else:
                db = sqlite3.connect(**self.kwargs)
            cursor = db.cursor()
            result = method(cursor)
            db.commit()

            return result
        finally:
            if cursor is not None:
                cursor.close()
            if self.db_ is None and db is not None:
                db.close()
            lock.release()


    def _initialize(self, cursor):
        cursor.execute('''CREATE TABLE tasks (id text, task_type text, payload text, date_posted timestamp, open int, result text)''')

    def _add(self, cursor, type, payload):
        id = str(uuid4())
        cursor.execute(
            'insert into tasks values (?,?,?,?,?,?)',
            (
                id,
                type,
                json.dumps(payload),
                datetime.now(),
                1,
                'null'
            ))
        return id


    def add(self, type: str, payload: Any) -> str:
        return self._perform(partial(self._add, type=type, payload=payload))


    def _construct_where(self, options: Optional[SearchOptions] = None) -> str:
        if options is None:
            return ''
        where = 'where True '
        if options.id is not None:
            where += f" and id = '{options.id}'"
        if options.type is not None:
            where += f" and task_type = '{options.type}'"
        if options.open is not None:
            if options.open:
                where += ' and open = 1'
            else:
                where += ' and open = 0'
        return where

    def _read(self, cursor, options):
        result = []
        where = self._construct_where(options)
        for row in cursor.execute('select * from tasks ' + where + " order by date_posted"):
            task = Message(
                row[0],
                row[1],
                json.loads(row[2]),
                row[3],
                row[4] == 1,
                json.loads(row[5])
            )
            result.append(task)
        return result

    def read(self, options: Optional[SearchOptions] = None) -> List[Message]:
        return self._perform(partial(self._read, options = options))

    def _close(self, cursor, id, result):
        cursor.execute('update tasks set open=?, result=? where id=?', (
            0,
            json.dumps(result),
            id
        ))


    def close(self, id: str, result: Any):
        self._perform(partial(self._close, id = id, result = result))

