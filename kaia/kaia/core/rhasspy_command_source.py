from .kaia_driver import ICommandSource, LogWriter, Queue
from ...avatar.dub.core import RhasspyAPI
from websocket import create_connection
import json
from threading import Thread

class RhasspyCommandSource(ICommandSource):
    def __init__(self, rhasspy_api: RhasspyAPI):
        self.rhasspy_api = rhasspy_api

    def start(self, queue: Queue, log_writer: LogWriter):
        Thread(target = self._run_intents_listener, args=(queue, log_writer), daemon=True).start()

    def _run_intents_listener(self, queue: Queue, log_writer: LogWriter):
        ws = create_connection(f"ws://{self.rhasspy_api.address}/api/events/intent")
        print("[RHASSPY] Web-socket open")
        while True:
            result = json.loads(ws.recv())
            log_writer.write('RhasspyIntentReceived', result)
            utterance = self.rhasspy_api.handler.parse_json(result)
            if utterance is None:
                log_writer.write('RhasspyIntentNotRecognized', result)
            else:
                queue.put(utterance)

    def get_name(self) -> str:
        return 'RhasspySource'