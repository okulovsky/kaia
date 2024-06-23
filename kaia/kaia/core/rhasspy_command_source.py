from .kaia_driver import ICommandSource, Queue
from .kaia_log import KaiaLog
from ...avatar.dub.core import RhasspyAPI
from websocket import create_connection
import json
from threading import Thread

class RhasspyCommandSource(ICommandSource):
    def __init__(self, rhasspy_api: RhasspyAPI):
        self.rhasspy_api = rhasspy_api

    def start(self, queue: Queue):
        Thread(target = self._run_intents_listener, args=(queue,), daemon=True).start()

    def _run_intents_listener(self, queue: Queue):
        ws = create_connection(f"ws://{self.rhasspy_api.address}/api/events/intent")
        KaiaLog.write('Rhasspy CS init', 'Web socket open')
        while True:
            result = json.loads(ws.recv())
            KaiaLog.write('Rhasspy intent received', result)
            utterance = self.rhasspy_api.handler.parse_json(result)
            if utterance is None:
                KaiaLog.write('Rhasspy intent not recognized', result)
            else:
                queue.put(utterance)

    def get_name(self) -> str:
        return 'RhasspySource'