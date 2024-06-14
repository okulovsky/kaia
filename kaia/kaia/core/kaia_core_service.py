from typing import *
from ...avatar.server import AvatarAPI
from ...avatar.dub.core import RhasspyAPI
from .kaia_driver import KaiaDriver
from ..gui import KaiaGuiApi, KaiaMessage
from abc import ABC, abstractmethod
from .kaia_assistant import KaiaAssistant

class RhasspyDriverSetup:
    def __init__(self,
                rhasspy_api: RhasspyAPI,
                kaia_api: KaiaGuiApi,
                train_rhasspy: bool = True,
                initial_volume: Optional[float] = 0.1
                 ):
        self.rhasspy_api = rhasspy_api
        self.kaia_api = kaia_api
        self.train_rhasspy = train_rhasspy
        self.initial_volume = initial_volume

    def __call__(self, core_service: 'KaiaCoreService'):
        if self.train_rhasspy:
            self.rhasspy_api.setup_intents(core_service.create_assistant().get_intents())
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy is training'))
            self.rhasspy_api.train()
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy has been trained'))

        if self.initial_volume is not None:
            self.rhasspy_api.set_volume(self.initial_volume)



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
        driver.run()


