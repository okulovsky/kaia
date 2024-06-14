import time

from .api import AudioControlAPI
from ...core import ICommandSource, LogWriter
from queue import Queue
from threading import Thread

class AudioControlCommandSource(ICommandSource):
    def __init__(self, api: AudioControlAPI):
        self.api = api

    def get_name(self) -> str:
        return 'AudioControl'

    def cycle(self,  queue: Queue, log_writer: LogWriter):
        log_writer.write('AudioControl source starts','')
        while True:
            command = self.api.wait_for_command()
            if command is None:
                continue
            print(f'[AudioControl] command received\n{command}')
            queue.put(command)

    def start(self, queue: Queue, log_writer: LogWriter):
        Thread(target = self.cycle, args=(queue, log_writer), daemon=True).start()

