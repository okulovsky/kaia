import atexit
import os
from typing import *
from ..sql_messenger import IMessenger, MessengerQuery
from ..loc import Loc
from .task_cycle import TaskCycle
from .task_processor import TaskProcessor, TaskStatus
from uuid import uuid4
import multiprocessing

class SqlTaskProcessor(TaskProcessor):
    def __init__(self, messenger: IMessenger):
        self.messenger = messenger

    def create_task(self, task_arguments: Any) -> str:
        id = str(uuid4())
        self.messenger.add(None, 'received', id)
        self.messenger.add(task_arguments, 'arguments', id)
        return id

    def get_active_tasks(self) -> List[str]:
        messages = MessengerQuery(tags=['received'], open=True).query(self.messenger)
        return [c.tags[1] for c in messages]

    def get_status(self, task_id: str) -> TaskStatus:
        return TaskCycle.gather_status(self.messenger, task_id)

    def is_finished(self, task_id: str) -> bool:
        return not MessengerQuery(tags=['received', task_id]).query_single(self.messenger).open

    def abort_task(self, task_id: str):
        open_message = MessengerQuery(tags=['received',task_id]).query_single(self.messenger)
        self.messenger.close(open_message.id, None)
        self.messenger.add(None, 'aborted', task_id)

    def get_debug_messages_table(self):
        return self.messenger._read_raw()






