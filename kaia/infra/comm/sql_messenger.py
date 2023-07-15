import datetime

import dateutil.parser

from .i_messenger import *
from .i_sql_connection import ISqlConnection
from uuid import uuid4
import jsonpickle
from functools import partial


class SqlMessenger(IMessenger):
    def __init__(self, connection: ISqlConnection, table_name: Optional[str] = None):
        if table_name is None:
            table_name = 'messenger'
        self.table_name = table_name
        self.tag_count = 10
        self.non_tag_column_count = 6
        self.connection = connection
        self.connection.perform(self._initialize)

    def _convert_tags(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        else:
            tags = list(tags)
        result = []
        for i in range(self.tag_count):
            if len(tags)>i:
                if tags[i] is None:
                    result.append([])
                elif isinstance(tags[i], str):
                    result.append([tags[i]])
                else:
                    result.append(list(tags[i]))
            else:
                result.append([])
        return result


    def _initialize(self, cursor):
        tags = ', '.join(f'tag_{i} text' for i in range(self.tag_count))
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.table_name} (id text, payload text, date_posted timestamp, open int, result text, tag_count int, {tags})''')

    def _add(self, cursor, payload, tags):
        id = str(uuid4())
        qlist = ','.join(['?' for _ in range(self.non_tag_column_count+self.tag_count)])

        all_tags = [None for _ in range(self.tag_count)]
        for i, t in enumerate(tags):
            all_tags[i] = t
        cursor.execute(
            f'insert into {self.table_name} values ({qlist})',
            (
                id,
                jsonpickle.dumps(payload),
                datetime.now(),
                1,
                'null',
                len(tags),
                *all_tags,
            ))
        return id


    def add(self, payload: Any, *tags: str) -> str:
        return self.connection.perform(partial(self._add, tags=tags, payload=payload))


    def _construct_where(self, options: Optional[MessengerQuery] = None) -> str:
        if options is None:
            return ''
        ands = ['True']
        if options.id is not None:
            ands.append(f"id = '{options.id}'")
        if options.tags is not None:
            for i, t in enumerate(self._convert_tags(options.tags)):
                current = []
                for tt in t:
                    current.append(f"tag_{i} = '{tt}'")
                if len(current)>0:
                    ands.append('('+' or '.join(current)+')')
        if options.open is not None:
            if options.open:
                ands.append('open = 1')
            else:
                ands.append('open = 0')
        where = ' where ' + ' and '.join(ands)
        return where

    def _read(self, cursor, query, raw = False):
        result = []
        where = self._construct_where(query)
        for row_values in cursor.execute(f'select * from {self.table_name} {where} order by date_posted'):
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
            if isinstance(task.date_posted, str): #TODO: why does this happen??
                task.date_posted = dateutil.parser.parse(task.date_posted)
            result.append(task)
        return result

    def read(self, query: Optional[MessengerQuery] = None) -> List[Message]:
        return self.connection.perform(partial(self._read, query = query))

    def _read_raw(self, query: Optional[MessengerQuery] = None) -> List[Dict]:
        return self.connection.perform(partial(self._read, query = query, raw = True))

    def _close(self, cursor, id, result):
        cursor.execute(f'update {self.table_name} set open=?, result=? where id=?', (
            0,
            jsonpickle.dumps(result),
            id
        ))


    def close(self, id: str, result: Any):
        self.connection.perform(partial(self._close, id = id, result = result))

