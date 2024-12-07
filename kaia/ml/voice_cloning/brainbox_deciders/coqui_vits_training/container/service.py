from pathlib import Path
import os
from abc import ABC, abstractmethod
import time
from threading import Thread
import traceback

class Service(ABC):
    def __init__(self,
                 folder: Path,
                 sleep_in_seconds: int = 60
                 ):
        self.folder = folder
        self.sleep_in_seconds = sleep_in_seconds

    @abstractmethod
    def _iteration(self):
        pass

    def get_name(self):
        return type(self).__name__



    def _monitoring(self):
        print(f'{self.get_name()} starts')
        while True:
            time.sleep(self.sleep_in_seconds)
            try:
                self._iteration()
            except:
                print(f'Exception in {self.get_name()}\n\n{traceback.format_exc()}')


    def run_monitoring(self):
        thread = Thread(target=self._monitoring, daemon=True)
        thread.start()
