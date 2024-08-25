from typing import *
from kaia.brainbox import BrainBoxApi, BrainBoxTask
from .kaia_driver import KaiaDriver
from ..gui import KaiaGuiApi, KaiaMessage
from abc import ABC, abstractmethod
from .kaia_assistant import KaiaAssistant

class RhasspyDriverSetup:
    def __init__(self,
                 brainbox_api: BrainBoxApi,
                 kaia_api: KaiaGuiApi,
                 train_rhasspy: bool = True,
                 initial_volume: Optional[float] = 0.1
                 ):
        self.brainbox_api = brainbox_api
        self.kaia_api = kaia_api
        self.train_rhasspy = train_rhasspy
        self.initial_volume = initial_volume

    def __call__(self, core_service: 'KaiaCoreService'):
        if self.train_rhasspy:
            intents = core_service.create_assistant().get_intents()
            task = BrainBoxTask(
                id = BrainBoxTask.safe_id(),
                decider='Rhasspy',
                decider_method='train',
                arguments=dict(intents=intents)
            )
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy is training'))
            self.brainbox_api.execute(task)
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy has been trained'))



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


