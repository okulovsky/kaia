from typing import *
from ..comm import IMessenger, MessengerQuery
from .progress_reporter import ProgressReporter, IProgressReporter
import traceback
import time
import sys
import dataclasses

@dataclasses.dataclass()
class TaskResult:
    id: str
    received: bool = False
    arguments: Dict[str,Any] = dataclasses.field(default_factory=lambda:{})
    accepted: bool = False
    progress: Optional[float] = None
    aborted: bool = False
    success: bool = False
    failure: bool = False
    result: Optional = None
    error: Optional[Dict[str,str]] = None
    log: Optional[List[str]] = dataclasses.field(default_factory=lambda:[])

    def finished(self):
        return self.aborted or self.success or self.failure

    def status(self):
        if self.aborted:
            return 'aborted'
        if self.success:
            return 'success'
        if self.failure:
            return 'failure'
        if self.accepted:
            return 'accepted'
        if self.received:
            return 'received'
        return 'unknown'


class ITask:
    def run(self, reporter: IProgressReporter, *args, **kwargs):
        raise NotImplementedError()

    def warm_up(self):
        pass


class TaskCycle:
    def __init__(self,
                 task: ITask,
                 sleep: float = 1.
                 ):
        self.task = task
        self.sleep = sleep

    def run(self, messenger: IMessenger):
        ProgressReporter(None, messenger).process_externals()
        self.task.warm_up()
        while True:
            ProgressReporter(None,messenger).process_externals()
            open_tasks_messages = MessengerQuery(tags=['received'], open=True).query(messenger)
            if len(open_tasks_messages)==0:
                time.sleep(self.sleep)
                continue
            message = open_tasks_messages[0]
            task_id = message.tags[1]
            reporter = ProgressReporter(task_id, messenger)
            arguments = MessengerQuery(tags=['arguments',task_id]).query_single(messenger).payload
            if arguments is None:
                arguments = {}
            try:
                messenger.add(None, 'accepted', task_id)
                result = self.task.run(reporter, **arguments)
                messenger.add(None, 'success', task_id)
                messenger.add(result, 'result', task_id)
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = dict(type = str(exc_type), value = str(exc_obj), trace = traceback.format_exc())
                messenger.add(None, 'failure', task_id)
                messenger.add(error, 'error', task_id)
            finally:
                messenger.close(message.id, None)


    @staticmethod
    def gather_status(messenger: IMessenger, task_id: str):
        info = TaskResult(task_id)
        for message in MessengerQuery(tags=[None,task_id]).query(messenger):
            if message.tags[0] in {'received', 'accepted', 'success', 'failure', 'aborted'}:
                setattr(info, message.tags[0], True)
            elif message.tags[0] in {'result','error','progress','arguments'}:
                setattr(info, message.tags[0], message.payload)
            elif message.tags[0] == 'log':
                info.log.append(message.payload)
            else:
                raise ValueError(f"Unknown tag `{message.tags[0]}` is associated with task {task_id}")
        return info



