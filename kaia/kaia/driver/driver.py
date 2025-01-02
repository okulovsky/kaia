import time
from typing import *
from datetime import datetime
from eaglesong.core import IAutomaton
from .primitives import TimerTick, Start, AudioCommand, AudioPlayConfirmation
from .interpreter import KaiaInterpreter
from queue import Queue
from ..server import KaiaApi, Message, BusItem
import traceback
from pathlib import Path
from dataclasses import dataclass
from .kaia_log import KaiaLog



@dataclass
class KaiaContext:
    driver: 'KaiaDriver'


class KaiaDriver:
    def __init__(self,
                 automaton_factory: Callable[[KaiaContext], IAutomaton],
                 kaia_api: KaiaApi,
                 time_tick_frequency_in_seconds: Optional[int] = None,
                 log_file: Path | None = None
                 ):
        self.last_time_tick: Optional[datetime] = None
        self.time_tick_frequency_in_seconds = time_tick_frequency_in_seconds
        self.automaton_factory = automaton_factory
        self.interpreter: Optional[KaiaInterpreter] = None
        self.queue = Queue()
        self.kaia_api = kaia_api
        self.first_time = True
        KaiaLog.setup(log_file)

    def _process(self, item):
        if self.interpreter is None:
            context = KaiaContext(self)
            automaton = self.automaton_factory(context)
            self.interpreter = KaiaInterpreter(automaton, self.kaia_api)
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
            self.kaia_api.add_message(Message(Message.Type.Error, err))
            self.interpreter = None
            KaiaLog.write('Processing error', err)


    def update_to_internal_dto(self, update: BusItem):
        if update.type == 'command_audio':
            return AudioCommand(update.payload)
        if update.type == 'confirmation_audio':
            return AudioPlayConfirmation(update.payload)
        return None



    def run(self):
        KaiaLog.write('init', 'Entering driver')
        while True:
            now = datetime.now()
            if self.time_tick_frequency_in_seconds is not None:
                if self.last_time_tick is not None:
                    delta = (now - self.last_time_tick).total_seconds()
                    if delta <= self.time_tick_frequency_in_seconds:
                        self.last_time_tick = now
                        self._process(TimerTick())

            updates = self.kaia_api.pull_updates()
            for update in updates:
                command = self.update_to_internal_dto(update)
                self._process(command)
            time.sleep(0.1)








