import time
from typing import *
from ..comm import IMessenger, MessengerQuery
from .task_cycle import TaskCycle
from .task_processor_abc import ITaskProcessor, TaskResult
from uuid import uuid4

class TaskProcessor(ITaskProcessor):
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

    def get_status(self, task_id: str) -> TaskResult:
        return TaskCycle.gather_status(self.messenger, task_id)

    def is_finished(self, task_id: str) -> bool:
        return not MessengerQuery(tags=['received', task_id]).query_single(self.messenger).open

    def abort_task(self, task_id: str):
        open_message = MessengerQuery(tags=['received',task_id]).query_single(self.messenger)
        self.messenger.close(open_message.id, None)
        self.messenger.add(None, 'aborted', task_id)

    def get_debug_messages_table(self):
        if hasattr(self.messenger, '_read_raw'):
            return self.messenger._read_raw()
        else:
            return None

    def is_alive(self, timeout_in_seconds):
        task_id = self.messenger.add(None, 'is_alive')
        for i in range(timeout_in_seconds):
            task = MessengerQuery(task_id).query_single(self.messenger)
            time.sleep(1)
            if not task.open:
                return True
        return False
