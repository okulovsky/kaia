from typing import *
from .decider import IDecider
from ...infra.comm import IMessenger
from .progress_reporter import MessengerProgressReporter
from .job import BrainBoxJob
import traceback
from threading import Thread
import time
from yo_fluq_ds import Query
from dataclasses import dataclass
from datetime import datetime
from .brain_box_log import LogFactory
from pathlib import Path
import jsonpickle
import json

@dataclass
class DeciderState:
    name: str
    up: bool = False
    busy: bool = False
    not_busy_since: Optional[datetime] = None


class DeciderInstance:
    def __init__(self,
                 name: str,
                 decider: IDecider,
                 logger: LogFactory,
                 file_cache: Path,
                 waiting_time_in_seconds: int = 5
                 ):
        self.state = DeciderState(name)
        self.decider = decider
        self.logger = logger
        self.file_cache = file_cache
        self.messenger = None #type: Optional[IMessenger]
        self.thread = None #type: Optional[Thread]
        self._exit_request = False
        self.waiting_time_in_seconds = waiting_time_in_seconds

    def warm_up(self, messenger: IMessenger):
        if self.state.up:
            raise ValueError('Service is already up')
        self.messenger = messenger
        self.logger.decider(self.state.name).event('Warming up')
        self.decider._setup_environment(self.file_cache, None)
        self.decider.warmup()
        self._exit_request = False
        self.thread = Thread(target=self.cycle)
        self.thread.start()
        self.state.up = True
        self.state.busy = False
        self.logger.decider(self.state.name).event('Warmed up')


    def cool_down(self):
        if not self.state.up:
            raise ValueError('Service is already down')
        self.logger.decider(self.state.name).event('Cooling down')
        self._exit_request = True

        self.logger.decider(self.state.name).event('Waits for cycle exit')
        for i in range(self.waiting_time_in_seconds*10):
            if not self.thread.is_alive():
                break
            time.sleep(0.1)

        if self.thread.is_alive():
            raise ValueError('Cannot exit thread gracefully')

        self.thread = None

        self.logger.decider(self.state.name).event('Exited cycle, external cooldown request')
        self.decider.cooldown()

        self.state.up = False
        self.state.busy = False
        self.logger.decider(self.state.name).event('Cooled down')


    def cycle(self):
        while True:
            if self._exit_request:
                break
            success = self.iteration()
            if not success:
                time.sleep(0.1)


    def failure(self, message, msg):
        msg += "\n"+traceback.format_exc()
        self.messenger.add(None, 'failure', message.tags[1])
        self.messenger.add(msg, 'error', message.tags[1])
        self.messenger.close(message.id, None)

    def iteration(self):
        open_request_messages = IMessenger.Query(tags=['received'], open=True).query(self.messenger)
        valid_messages = Query.en(open_request_messages).where(lambda z: z.payload['decider'] == self.state.name).to_list()

        if len(valid_messages) == 0:
            if self.state.busy:
                self.state.busy = False
                self.state.not_busy_since = datetime.now()
                self.logger.decider(self.state.name).event('Not busy')
            return False

        if not self.state.busy:
            self.state.busy = True
            self.logger.decider(self.state.name).event('Busy')

        message = open_request_messages[0]
        id = message.tags[1]
        self.logger.decider(self.state.name).event(f'Processing task {id}')


        method = message.payload['method']
        arguments = message.payload['arguments']

        self.messenger.add(None, 'accepted', id)
        self.logger.task(id).event('Accepted')

        reporter = MessengerProgressReporter(id, self.messenger)
        self.decider._setup_environment(self.file_cache, reporter)
        try:
            result = getattr(self.decider,method)(**arguments)
            self.messenger.add(result, 'result', id)
            self.messenger.close(message.id, None)
            self.messenger.add(None, 'success', id)
            self.logger.task(id).event('Finished with a success')
        except:
            self.failure(message, "Executing")
            self.logger.task(id).event('Finished with a failure')
            return False
        return True


    @staticmethod
    def collect_status(task: BrainBoxJob, messenger: IMessenger):
        messages = messenger.Query(tags=[None, task.id]).query(messenger)
        log = []
        for message in messages:
            tag = message.tags[0]

            if tag == 'accepted':
                task.accepted = True
                task.accepted_timestamp = message.date_posted
                continue

            if tag == 'success':
                task.finished = True
                task.success = True
                task.finished_timestamp = message.date_posted
                continue

            if tag == 'failure':
                task.finished = True
                task.success = False
                task.finished_timestamp = message.date_posted
                continue

            if tag == 'error':
                task.error = message.payload
                continue

            if tag == 'result':
                task.result = json.loads(jsonpickle.dumps(message.payload))
                continue

            if tag == 'progress':
                task.progress = message.payload
                continue

            if tag == 'log':
                log.append(message.payload)
                continue

        task.log = log


