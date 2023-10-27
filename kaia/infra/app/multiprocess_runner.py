from typing import *
import multiprocessing
from .runner import IRunner
from ..loc import Loc

class MultiprocessingRunner(IRunner):
    def __init__(self, entry: Callable):
        self.entry = entry
        self.process = None #type: Optional[multiprocessing.Process]

    def run(self):
        if Loc.is_windows:
            raise ValueError('Multiprocessing does not work under windows')
        self.process = multiprocessing.Process(target=self.entry)
        self.process.start()

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None
