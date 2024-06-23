import time

from .api import AudioControlAPI
from ...core import ICommandSource, KaiaLog
from queue import Queue
from threading import Thread

class AudioControlCommandSource(ICommandSource):
    def __init__(self, api: AudioControlAPI):
        self.api = api

    def get_name(self) -> str:
        return 'AudioControl'

    def cycle(self,  queue: Queue):
        KaiaLog.write('AudioControl source starts','')
        while True:
            command = self.api.wait_for_command()
            if command is None:
                continue
            KaiaLog.write('AudioControl command received', command)
            queue.put(command)

    def start(self, queue: Queue):
        Thread(target = self.cycle, args=(queue,), daemon=True).start()

