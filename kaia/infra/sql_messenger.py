from typing import *
import jsonpickle
from datetime import datetime
from uuid import uuid4
import sqlite3
import os
from functools import partial
from pathlib import Path
import dataclasses

@dataclasses.dataclass
class Message:
     id: str
     payload: Any
     date_posted: Optional[datetime]
     open: bool
     result: Any
     tags: Tuple



class MessengerQuery:
    def __init__(self,
                 id: Optional[str] = None,
                 open: Optional[bool] = None,
                 tags: Union[None, str, Iterable[str]] = None,
        ):
        self.id = id
        self.open = open
        self.tags = tags

    def query(self, messenger: 'IMessenger') -> List[Message]:
        return messenger.read(self)

    def query_single(self, messenger: 'IMessenger') -> Message:
        result = self.query(messenger)
        if len(result)!=1:
            raise ValueError(f"Request for id `{self.id}`, tags `{self.tags}`, open `{self.open}` returned {len(result)} tasks, 1 was expected")
        return result[0]

    def query_count(self, messenger: 'IMessenger') -> int:
        return len(self.query(messenger))


class IMessenger:
    def add(self, payload: Any, *tags: str) -> str:
        raise NotImplementedError()

    def read(self, query: Optional[MessengerQuery] = None) -> List[Message]:
        raise NotImplementedError()

    def close(self, id: str, payload: Any):
        raise NotImplementedError()

    def read_all_and_close(self, tags: Union[None, str, Iterable[str]] = None) -> List[Message]:
        tasks = self.read(MessengerQuery(tags = tags, open=True))
        for t in tasks:
            self.close(t.id, None)
        return tasks


import threading

lock = threading.Lock()


class SqlMessenger(IMessenger):
    def __init__(self, location: Optional[str] = None, reset_if_existed = False):
        self.tag_count = 10
        self.non_tag_column_count = 6
        if location is None:
            self.kwargs = dict(database = ':memory:', check_same_thread = False)
            self.db_ = sqlite3.connect(**self.kwargs)
        else:
            if reset_if_existed and os.path.isfile(location):
                os.remove(location)
            os.makedirs(Path(location).parent, exist_ok=True)
            self.kwargs = dict(database = location)
            self.db_ = None
        self._perform(self._initialize)

    def _convert_tags(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        else:
            tags = list(tags)
        result = []
        for i in range(self.tag_count):
            if len(tags)>i:
                result.append(tags[i])
            else:
                result.append(None)
        return result


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
        tags = ', '.join(f'tag_{i} text' for i in range(self.tag_count))
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS tasks (id text, payload text, date_posted timestamp, open int, result text, tag_count int, {tags})''')

    def _add(self, cursor, payload, tags):
        id = str(uuid4())
        qlist = ','.join(['?' for _ in range(self.non_tag_column_count+self.tag_count)])

        cursor.execute(
            f'insert into tasks values ({qlist})',
            (
                id,
                jsonpickle.dumps(payload),
                datetime.now(),
                1,
                'null',
                len(tags),
                *self._convert_tags(tags),
            ))
        return id


    def add(self, payload: Any, *tags: str) -> str:
        return self._perform(partial(self._add, tags=tags, payload=payload))


    def _construct_where(self, options: Optional[MessengerQuery] = None) -> str:
        if options is None:
            return ''
        where = 'where True '
        if options.id is not None:
            where += f" and id = '{options.id}'"
        if options.tags is not None:
            for i, t in enumerate(self._convert_tags(options.tags)):
                if t is not None:
                    where += f" and tag_{i} = '{t}'"
        if options.open is not None:
            if options.open:
                where += ' and open = 1'
            else:
                where += ' and open = 0'
        return where

    def _read(self, cursor, query, raw = False):
        result = []
        where = self._construct_where(query)
        for row_values in cursor.execute('select * from tasks ' + where + " order by date_posted"):
            row = {k[0]:v for k, v in zip(cursor.description, row_values)}
            if raw:
                result.append(row)
                continue
            tags = []
            for i in range(row['tag_count']):
                tags.append(row[f'tag_{i}'])
            task = Message(
                row['id'],
                jsonpickle.loads(row['payload']),
                row['date_posted'],
                row['open'],
                jsonpickle.loads(row['result']),
                tags
            )
            result.append(task)
        return result

    def read(self, query: Optional[MessengerQuery] = None) -> List[Message]:
        return self._perform(partial(self._read, query = query))

    def _read_raw(self, query: Optional[MessengerQuery] = None) -> List[Dict]:
        return self._perform(partial(self._read, query = query, raw = True))

    def _close(self, cursor, id, result):
        cursor.execute('update tasks set open=?, result=? where id=?', (
            0,
            jsonpickle.dumps(result),
            id
        ))


    def close(self, id: str, result: Any):
        self._perform(partial(self._close, id = id, result = result))

