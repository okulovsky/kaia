import time
from typing import *
from datetime import datetime
from eaglesong.core import IAutomaton
from .primitives import TimerTick, InitializationCommand, AudioCommand, AudioPlayConfirmation
from ..server.buttons import ButtonPressedEvent
from .interpreter import KaiaInterpreter
from queue import Queue
from ..server import KaiaApi, Message, BusItem
import traceback
from pathlib import Path
from dataclasses import dataclass
from .kaia_log import KaiaLog
from avatar import AvatarApi



@dataclass
class KaiaContext:
    driver: Optional['KaiaDriver'] = None
    avatar_api: AvatarApi|None = None


class KaiaDriver:
    def __init__(self,
                 automaton_factory: Callable[[KaiaContext], IAutomaton],
                 kaia_api: KaiaApi,
                 time_tick_frequency_in_seconds: Optional[int] = None,
                 log_file: Path | None = None,
                 avatar_api: AvatarApi|None = None,
                 ):
        self.last_time_tick: Optional[datetime] = None
        self.time_tick_frequency_in_seconds = time_tick_frequency_in_seconds
        self.automaton_factory = automaton_factory
        self.interpreter: Optional[KaiaInterpreter] = None
        self.queue = Queue()
        self.kaia_api = kaia_api
        self.first_time = True
        self.avatar_api = avatar_api
        KaiaLog.setup(log_file)

    def _process(self, item):
        KaiaLog.write(f"Processing item", str(item))
        if self.interpreter is None:
            KaiaLog.write(f"Creating interpreter",'')
            context = KaiaContext(self, self.avatar_api)
            automaton = self.automaton_factory(context)
            self.interpreter = KaiaInterpreter(automaton, self.kaia_api)
            KaiaLog.write(f"Created interpreter",'')
        try:
            KaiaLog.write("Item to interpreter", str(item))
            self.interpreter.process(item)
        except:
            err = traceback.format_exc()
            self.kaia_api.add_message(Message(Message.Type.Error, err))
            self.interpreter = None
            KaiaLog.write('Processing error', err)


    def update_to_internal_dto(self, update: BusItem):
        KaiaLog.write("Checking update", str(update))
        if update.type == 'command_audio':
            return AudioCommand(update.payload)
        if update.type == 'confirmation_audio':
            return AudioPlayConfirmation(update.payload)
        if update.type == 'command_initialize':
            return InitializationCommand()
        if update.type == 'command_button':
            return ButtonPressedEvent(update.payload)

        return None



    def run(self):
        KaiaLog.write('init', 'Entering driver')
        while True:
            updates = self.kaia_api.pull_updates()
            for update in updates:
                command = self.update_to_internal_dto(update)
                if command is not None:
                    self._process(command)

            now = datetime.now()
            if self.time_tick_frequency_in_seconds is not None:
                if self.last_time_tick is not None:
                    delta = (now - self.last_time_tick).total_seconds()
                else:
                    delta = None
                if delta is None or delta > self.time_tick_frequency_in_seconds:
                    self.last_time_tick = now
                    self._process(TimerTick())


            time.sleep(0.1)








