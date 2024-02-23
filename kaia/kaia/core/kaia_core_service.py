from typing import *
from ...avatar.server import AvatarAPI
from ...avatar.dub.core import RhasspyAPI
from .utterances_translator import UtterancesTranslator
from .utterances_presenter import UtterancesPresenter
from .volume_translator import VolumeTranslator
from .kaia_driver import KaiaDriver
from .kaia_server import KaiaApi, KaiaMessage
from ...eaglesong.core import Automaton



class KaiaCoreService:
    def __init__(self,
                 assistant_factory,
                 avatar_api: AvatarAPI,
                 rhasspy_api: RhasspyAPI,
                 kaia_api: KaiaApi,
                 train_rhasspy: bool = False,
                 initial_volume: Optional[float] = 0.1,
                 driver_kwargs: Optional[Dict] = None
                 ):
        self.assistant_factory = assistant_factory
        self.avatar_api = avatar_api
        self.rhasspy_api = rhasspy_api
        self.kaia_api = kaia_api
        self.train_rhasspy = train_rhasspy
        self.initial_volume = initial_volume
        self.driver_kwargs = driver_kwargs if driver_kwargs is not None else {}


    def factory(self, context):
        assistant = self.assistant_factory()
        assistant = UtterancesTranslator(assistant, self.rhasspy_api, self.avatar_api)
        assistant = UtterancesPresenter(assistant, self.kaia_api)
        assistant = VolumeTranslator(assistant, self.rhasspy_api.set_volume, self.initial_volume)
        return Automaton(assistant, context)


    def __call__(self):
        assistant = self.assistant_factory()
        self.rhasspy_api.setup_intents(assistant.get_intents())
        if self.train_rhasspy:
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy is training'))
            self.rhasspy_api.train()
            self.kaia_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy has been trained'))
        if self.initial_volume is not None:
            self.rhasspy_api.set_volume(self.initial_volume)
        driver = KaiaDriver(self.factory, self.rhasspy_api, self.kaia_api, **self.driver_kwargs)
        driver.run()


