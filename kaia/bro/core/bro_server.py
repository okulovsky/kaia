import time
from typing import *
from .bro_algorithm import BroAlgorithm
from dataclasses import dataclass
from datetime import datetime
from ...infra.comm import IStorage, IMessenger, MessengerQuery, FakeStorage, FakeMessenger, Sql
from ...infra.app import KaiaApp

from yo_fluq_ds import Query
import time
from .bro_client import BroClient, StorageClientDataProvider
import threading
import multiprocessing
import atexit


@dataclass
class AlgorithmState:
    enabled: bool = True
    last_call: Optional[datetime] = None


class BroServer:
    def __init__(self,
                 algorithms: Iterable[BroAlgorithm],
                 pause_in_milliseconds: int = 0,
                 iterations_limit: Optional[int] = None,
                 ):
        self.algorithms = list(algorithms)
        self.pause_in_milliseconds = pause_in_milliseconds
        self.iterations_limit = iterations_limit

        self.states = None  # type: Optional[Dict[str, AlgorithmState]]
        self.last_track = {}

    def run(self,
            storage: Optional[IStorage] = None,
            messenger: Optional[IMessenger] = None,
            ):
        if storage is None:
            storage = FakeStorage()
        if messenger is None:
            messenger = FakeMessenger()
        self.states = {alg.space.get_name(): AlgorithmState() for alg in self.algorithms}
        last_stored = storage.load('bro_server_enabled', 1)
        if len(last_stored) > 0:
            for key, value in last_stored[0].items():
                if key in self.states:
                    self.states[key] = value
        for alg in self.algorithms:
            alg.start_up(storage, messenger)
        iteration_num = 0
        while True:
            if not self.iteration(storage, messenger):
                break
            iteration_num+=1
            if self.iterations_limit is not None and iteration_num>self.iterations_limit:
                break
            time.sleep(self.pause_in_milliseconds/1000)

    def run_in_multiprocess(self, storage: Optional[IStorage] = None, messenger: Optional[IMessenger] = None):
        p = multiprocessing.Process(target=self.run, args=[storage, messenger])
        p.start()
        atexit.register(lambda: p.kill())
        return p

    def iteration(self, storage: IStorage, messenger: IMessenger):
        messages = MessengerQuery(open=True, tags=['to', 'bro_server', 'terminate']).query(messenger)
        if len(messages) > 0:
            return False

        messages = MessengerQuery(open=True, tags=['to', None, ('enable', 'disable')]).query(messenger)
        has_change = False
        for message in messages:
            if message.tags[1] in self.states:
                self.states[message.tags[1]].enabled = message.tags[2]=='enable'
                has_change = True
        if has_change:
            storage.save('bro_server_enabled', {k: v.enabled for k, v in self.states.items()})

        self.last_track = {}
        now = datetime.now()
        run_times = {}
        for algorithm in self.algorithms:
            if not self.states[algorithm.space.get_name()].enabled:
                continue
            if self.states[algorithm.space.get_name()].last_call is not None:
                delta = now - self.states[algorithm.space.get_name()].last_call
                if 1000*delta.total_seconds() < algorithm.update_interval_in_milliseconds:
                    continue
            begin = datetime.now()
            algorithm.iterate(storage, messenger)
            end = datetime.now()
            self.states[algorithm.space.get_name()].last_call = begin
            run_times[algorithm.space.get_name()] = (end-begin).total_seconds()

        if len(run_times)>0:
            storage.save('bro_server_stats', run_times)

        return True


    def create_client(self, algorithm: BroAlgorithm, storage: IStorage, messenger: IMessenger):
        puller = StorageClientDataProvider(
            algorithm.space.get_name(),
            storage,
            algorithm.max_history_length)
        return BroClient(algorithm.space, puller, messenger)

