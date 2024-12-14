from typing import *
from kaia.brainbox import BrainBoxApi, BrainBoxTask
from .kaia_driver import KaiaDriver
from ..gui import KaiaGuiApi, KaiaMessage
from abc import ABC, abstractmethod
from .kaia_assistant import KaiaAssistant

class KaiaCoreService(ABC):
    @abstractmethod
    def create_assistant(self) -> KaiaAssistant:
        pass


    @abstractmethod
    def create_driver(self) -> KaiaDriver:
        pass


    @abstractmethod
    def pre_run_setup(self):
        pass


    def __call__(self):
        self.pre_run_setup()
        driver = self.create_driver()
        self._ready = True
        driver.run()


