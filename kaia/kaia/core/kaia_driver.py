import time
from typing import *
from datetime import datetime
from kaia.eaglesong.core import primitives as prim, IAutomaton
from .kaia_interpreter import KaiaInterpreter
from queue import Queue
from ..gui import KaiaGuiApi, KaiaMessage
import traceback
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .kaia_log import KaiaLog

@dataclass
class Start:
    first_time: bool


@dataclass
class KaiaContext:
    driver: 'KaiaDriver'





class ICommandSource(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def start(self, queue: Queue):
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
                 log_file: Path|None = None
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
        self.first_time = True
        KaiaLog.setup(log_file)


    def _process(self, item):
        if self.interpreter is None:
            context = KaiaContext(self)
            automaton = self.automaton_factory(context)
            self.interpreter = KaiaInterpreter(automaton, self.audio_play_function, self.kaia_api)
            try:
                self.interpreter.process(Start(self.first_time))
                self.first_time = False
            except:
                err = traceback.format_exc()
                KaiaLog.write('First-time start error', err)

        try:
            self.interpreter.process(item)
        except:
            err = traceback.format_exc()
            self.kaia_api.add_message(KaiaMessage(True, err, True))
            self.interpreter = None
            KaiaLog.write('Processing error', err)

    def run(self):
        KaiaLog.write('init', 'Entering driver')
        for source in self.command_sources:
            KaiaLog.write('init', f'Starting {source.get_name()}')
            source.start(self.queue)
            KaiaLog.write('init', f'Started {source.get_name()}')
        KaiaLog.write('init', 'Entering the main cycle')
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








