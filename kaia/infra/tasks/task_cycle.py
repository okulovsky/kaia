from typing import *
from ..sql_messenger import IMessenger, MessengerQuery
from .task_processor import TaskStatus
from datetime import datetime
import sys
import traceback
import time
import os
import sys

class AbortedException(Exception):
    def __init__(self):
        super(AbortedException, self).__init__('Task was aborted')


class ProgressReporter:
    def __init__(self, id: str, messenger: IMessenger):
        self.id = id
        self.messenger = messenger

    def process_externals(self):
        self.messenger.read_all_and_close('is_alive')
        terminate = self.messenger.read_all_and_close('terminate')
        if len(terminate) > 0:
            sys.exit()
        if self.id is not None:
            if MessengerQuery(tags=['aborted', self.id]).query_count(self.messenger) > 0:
                raise AbortedException()

    def report_progress(self, progress: float):
        self.process_externals()
        self.messenger.add(progress, 'progress', self.id)

    def log(self, s):
        self.process_externals()
        self.messenger.add(s, 'log', self.id)


class ITask:
    def run(self, reporter: ProgressReporter, *args, **kwargs):
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
        info = TaskStatus(task_id)
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



