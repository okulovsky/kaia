from typing import *
from .i_storage import IStorage, StorageRecord
from .i_sql_connection import ISqlConnection
import jsonpickle
from datetime import datetime
from functools import partial


class SqlStorage(IStorage):
    def __init__(self, connection: ISqlConnection, table_name: Optional[str] = None):
        self.connection = connection
        if table_name is None:
            table_name = 'storage'
        self.table_name = table_name
        self.connection.perform(self._initialize)

    def _initialize(self, cursor):
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {self.table_name} (id integer primary key, timestamp timestamp, key text, value text)''')

    def _save(self, cursor, key, value):
        cursor.execute(f'insert into {self.table_name} values(?, ?, ?, ?)',
                       (None,datetime.now(), key, value)
                       )

    def save(self, key: str, value: Any):
        value = jsonpickle.dumps(value)
        self.connection.perform(partial(self._save, key=key, value=value))

    def _load(self, cursor, key, amount, last_update_id, last_update_timestamp):
        sql = f'select id, timestamp, value from {self.table_name} '

        conditions = []
        arguments = []
        if key is not None:
            conditions.append('key = ?')
            arguments.append(key)
        if last_update_id is not None:
            conditions.append('id > ?')
            arguments.append(last_update_id)
        if last_update_timestamp is not None:
            conditions.append('timestamp > ?')
            arguments.append(last_update_timestamp)

        where = ' and '.join(conditions)
        if where!='':
            where = ' where ' + where
        sql += ' '+where+' '
        sql += 'order by id desc '
        if amount is not None:
            sql += f'limit {amount}'
        data = list(cursor.execute(sql, arguments))
        return data

    def load_update(self,
                   key: Optional[str] = None,
                   amount: Optional[int] = None,
                   last_update_id: Optional[int] = None,
                   last_update_timestamp: Optional[datetime] = None,
                   historical_order: bool = True
                   ) -> List[StorageRecord]:
        result = self.connection.perform(partial(self._load, key=key, amount=amount, last_update_id=last_update_id, last_update_timestamp=last_update_timestamp))
        if historical_order:
            result = reversed(result)
        return [StorageRecord(s[0], s[1], jsonpickle.loads(s[2])) for s in result]



