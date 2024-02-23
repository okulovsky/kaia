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
from .kaia_server import KaiaApi, KaiaMessage
import traceback
from pathlib import Path
from dataclasses import dataclass


lock = threading.Lock()


@dataclass
class KaiaContext:
    driver: 'KaiaDriver'

class KaiaDriver:
    def __init__(self,
                 automaton_factory: Callable[[KaiaContext], IAutomaton],
                 rhasspy_api: RhasspyAPI,
                 kaia_api: Optional[KaiaApi] = None,
                 time_tick_frequency_in_seconds: Optional[int] = None,
                 sleep_in_seconds: float = 0.1,
                 enable_time_tick: bool = False,
                 log_file: Optional[Path] = None
                 ):
        self.last_time_tick: Optional[datetime] = None
        self.time_tick_frequency_in_seconds = time_tick_frequency_in_seconds
        self.sleep_in_seconds = sleep_in_seconds
        self.automaton_factory = automaton_factory
        self.interpreter: Optional[KaiaInterpreter] = None
        self.rhasspy_api = rhasspy_api
        self.enable_time_tick = enable_time_tick
        self.queue = Queue()
        self.kaia_api = kaia_api
        self.log_file = log_file


    def _process(self, item):
        print(f'[MAIN] {item}')
        if self.interpreter is None:
            context = KaiaContext(self)
            automaton = self.automaton_factory(context)
            self.interpreter = KaiaInterpreter(automaton, self.rhasspy_api, self.kaia_api)
        try:
            self.interpreter.process(item)
        except:
            err = traceback.format_exc()
            self.kaia_api.add_message(KaiaMessage(True, err, True))
            self.interpreter = None

    def run(self):
        Thread(target=self._run_intents_listener, daemon=True).start()
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

    def write_log_entry(self, type, content):
        if self.log_file is not None:
            with lock:
                os.makedirs(self.log_file.parent, exist_ok=True)
                with open(self.log_file,'a') as file:
                    file.write(json.dumps(dict(type=type, timestamp=str(datetime.now()), content=content)))

    def _run_intents_listener(self):
        ws = create_connection(f"ws://{self.rhasspy_api.address}/api/events/intent")
        print("[RHASSPY] Web-socket open")
        while True:
            result = json.loads(ws.recv())
            self.write_log_entry('RhasspyIntentReceived', result)
            utterance = self.rhasspy_api.handler.parse_json(result)
            if utterance is None:
                self.write_log_entry('RhasspyIntentNotRecognized', result)
            else:
                self.queue.put(utterance)





    

