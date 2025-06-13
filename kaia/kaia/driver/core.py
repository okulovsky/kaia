from typing import *
from kaia.kaia import translators as kaia_translators
from kaia.kaia import audio_control as ac
from ..translators import *
from ..assistant import KaiaAssistant
from .driver import KaiaDriver
from ..server import KaiaApi, Message
from brainbox import BrainBoxApi, ControllersSetup
from avatar import AvatarApi
from pathlib import Path
from eaglesong.core import Automaton
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .kaia_log import KaiaLog



@dataclass
class KaiaCoreServiceSettings:
    avatar_api: AvatarApi
    audio_api: ac.AudioControlApi
    brainbox_api: BrainBoxApi
    kaia_api: KaiaApi
    brainbox_setup: ControllersSetup|None = None
    resemblyzer_model_name: str|None = None
    name_to_avatar_image: Optional[Callable[[str], str]] = None
    initial_volume: float = 0.1
    delay_for_ac_server: int = 10
    log_file: Path|None = None


class KaiaCoreService(ABC):
    def __init__(self, settings: KaiaCoreServiceSettings):
        self.settings = settings
        self.intents_ = []
        self.replies_ = []

    @abstractmethod
    def create_assistant(self) -> KaiaAssistant:
        pass


    def _volume_callback_stub(self, value):
        KaiaLog.write('Volume callback stub', value)

    def create_automaton(self, context):
        assistant = self.create_assistant()

        assistant = kaia_translators.VoiceoverTranslator(assistant, self.settings.avatar_api)
        assistant = kaia_translators.KaiaMessageTranslator(assistant, self.settings.kaia_api, self.settings.avatar_api, self.settings.name_to_avatar_image)
        if self.settings.audio_api is not None:
            volume_callback = self.settings.audio_api.set_volume
        else:
            volume_callback = self._volume_callback_stub

        assistant = kaia_translators.VolumeTranslator(assistant, volume_callback, self.settings.initial_volume)
        assistant = kaia_translators.RecognitionTranslator(assistant, self.settings.avatar_api)

        if self.settings.audio_api is not None:
            assistant = AudioControlSwitcherTranslator(assistant, self.settings.audio_api)

        return Automaton(assistant, context)


    def create_driver(self) -> KaiaDriver:
        return KaiaDriver(
            self.create_automaton,
            self.settings.kaia_api,
            time_tick_frequency_in_seconds=1,
            log_file=self.settings.log_file,
            avatar_api=self.settings.avatar_api
        )

    def pre_run_setup(self):
        self.settings.brainbox_api.wait()
        if self.settings.brainbox_setup is not None:
            self.settings.brainbox_api.controller_api.setup(self.settings.brainbox_setup)

        self.settings.avatar_api.wait()

        if self.settings.audio_api is not None:
            self.settings.audio_api.wait(self.settings.delay_for_ac_server)

        assistant = self.create_assistant()
        intents = tuple(assistant.get_intents())
        self.settings.kaia_api.add_message(Message(Message.Type.System, f"Training {len(intents)} Rhasspy models"))
        self.settings.avatar_api.recognition_train(intents)
        self.settings.avatar_api.dub_paraphrase_set_replies(assistant.get_replies())
        self.settings.kaia_api.add_message(Message(Message.Type.System, "Rhasspy is trained"))
        if self.settings.audio_api is not None:
            self.settings.audio_api.set_volume(self.settings.initial_volume)

    def __call__(self):
        self.settings.kaia_api.last_message_id = self.settings.kaia_api.bus.get_max_message_id(self.settings.kaia_api.session_id)
        self.pre_run_setup()
        driver = self.create_driver()
        self.settings.kaia_api.driver_starts(id(driver))
        self._ready = True
        driver.run()
