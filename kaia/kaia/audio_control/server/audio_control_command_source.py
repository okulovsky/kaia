import time
from .api import AudioControlAPI
from kaia.kaia.core import ICommandSource, KaiaLog
from queue import Queue
from threading import Thread
from dataclasses import dataclass

@dataclass
class AudioControlCommand:
    filename: str


class AudioControlCommandSource(ICommandSource):
    def __init__(self, api: AudioControlAPI):
        self.api = api

    def get_name(self) -> str:
        return 'AudioControl'

    def cycle(self,  queue: Queue):
        KaiaLog.write('AudioControl source starts','')
        while True:
            filename = self.api.wait_for_uploaded_filename()
            if filename is None:
                continue
            KaiaLog.write('AudioControl command received', filename)
            command = AudioControlCommand(filename)
            queue.put(command)

    def start(self, queue: Queue):
        Thread(target = self.cycle, args=(queue,), daemon=True).start()

