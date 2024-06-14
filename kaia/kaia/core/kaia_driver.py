import os
import threading
import time
from typing import *
from datetime import datetime
from kaia.eaglesong.core import primitives as prim, IAutomaton
from .kaia_interpreter import KaiaInterpreter
from kaia.avatar.dub.core import RhasspyAPI
from websocket import create_connection
from threading import Thread
import json
from queue import Queue
from ..gui import KaiaGuiApi, KaiaMessage
from .kaia_assistant import KaiaAssistant
import traceback
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Start:
    first_time: bool


lock = threading.Lock()


@dataclass
class KaiaContext:
    driver: 'KaiaDriver'


class LogWriter:
    def __init__(self, log_file):
        self.log_file = log_file

    def write(self, type, content):
        if self.log_file is not None:
            with lock:
                os.makedirs(self.log_file.parent, exist_ok=True)
                with open(self.log_file,'a') as file:
                    file.write(json.dumps(dict(type=type, timestamp=str(datetime.now()), content=content)))






class ICommandSource(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def start(self, queue: Queue, log_writer: LogWriter):
        pass



class KaiaDriver:
    def __init__(self,
                 automaton_factory: Callable[[KaiaContext], IAutomaton],
                 audio_play_function: Callable[[bytes], None],
                 command_sources: Iterable[ICommandSource],
                 kaia_api: Optional[KaiaGuiApi] = None,
                 time_tick_frequency_in_seconds: Optional[int] = None,
                 sleep_in_seconds: float = 0.1,
                 enable_time_tick: bool = False,
                 log_file: Optional[Path] = None,
                 ):
        self.command_sources = tuple(command_sources)
        self.last_time_tick: Optional[datetime] = None
        self.time_tick_frequency_in_seconds = time_tick_frequency_in_seconds
        self.sleep_in_seconds = sleep_in_seconds
        self.automaton_factory = automaton_factory
        self.interpreter: Optional[KaiaInterpreter] = None
        self.audio_play_function = audio_play_function
        self.enable_time_tick = enable_time_tick
        self.queue = Queue()
        self.kaia_api = kaia_api
        self.log_file = log_file
        self.first_time = True
        self.log_writer: None|LogWriter = None



    def _process(self, item):
        print(f'[MAIN] {item}')
        if self.interpreter is None:
            context = KaiaContext(self)
            automaton = self.automaton_factory(context)
            self.interpreter = KaiaInterpreter(automaton, self.audio_play_function, self.kaia_api)
            self.interpreter.process(Start(self.first_time))
            self.first_time = False
        try:
            self.interpreter.process(item)
        except:
            err = traceback.format_exc()
            self.kaia_api.add_message(KaiaMessage(True, err, True))
            self.interpreter = None

    def run(self):
        self.log_writer = LogWriter(self.log_file)
        for source in self.command_sources:
            print(f'Starting {source.get_name()}')
            source.start(self.queue, self.log_writer)
        print('[MAIN] entering main cycle')
        while True:
            now = datetime.now()
            if self.enable_time_tick:
                if self.last_time_tick is None or (now - self.last_time_tick).total_seconds() > self.time_tick_frequency_in_seconds:
                    self.last_time_tick = now
                    self._process(prim.TimerTick())

            while not self.queue.empty():
                element = self.queue.get()
                self._process(element)
                
            time.sleep(self.sleep_in_seconds)








