from typing import *
from kaia.kaia import core as kaia_core
from kaia.kaia import translators as kaia_translators
from kaia.kaia import audio_control as ac
from kaia.kaia.skills.change_image_skill import ChangeImageIntents
from kaia.kaia.skills.character_skill import ChangeCharacterIntents

from kaia.avatar import AvatarAPI
from pathlib import Path
from kaia.eaglesong.core import Automaton
from dataclasses import dataclass
from kaia.brainbox import BrainBoxApi



@dataclass
class KaiaCoreAudioControlServiceSettings:
    avatar_api: AvatarAPI
    kaia_api: kaia_core.KaiaGuiApi
    audio_api: ac.AudioControlAPI
    brainbox_api: BrainBoxApi

    resemblyzer_model_name: str|None = None
    name_to_avatar_image: Optional[Callable[[str], str]] = None

    initial_volume: float = 0.1
    delay_for_ac_server: int = 10
    log_file: Path|None = None


class KaiaCoreAudioControlService(kaia_core.KaiaCoreService):
    def __init__(self,
                 settings: KaiaCoreAudioControlServiceSettings
                 ):
        self.settings = settings
        self.intents_ = []
        self.replies_ = []
        self.audio_control_handler = kaia_translators.AudioControlHandler(
            self.settings.audio_api,
            self.settings.brainbox_api,
            self.settings.kaia_api,
            self._create_intents,
            self.settings.resemblyzer_model_name,
            self.settings.avatar_api
        )

    def _create_intents(self):
        return self.create_assistant().get_intents()

    def create_automaton(self, context):
        assistant = self.create_assistant()
        self.intents_ = assistant.get_intents()
        self.replies_ = assistant.get_replies()


        assistant = kaia_translators.InitializationWrap(
            assistant,
            [ChangeImageIntents.change_image.utter()],
            [ChangeCharacterIntents.change_character.utter()],
            False
        )

        assistant = kaia_translators.VoiceoverTranslator(assistant, self.settings.avatar_api)
        assistant = kaia_translators.KaiaMessageTranslator(assistant, self.settings.kaia_api, self.settings.avatar_api, self.settings.name_to_avatar_image)
        assistant = kaia_translators.VolumeTranslator(assistant, self.settings.audio_api.set_volume, self.settings.initial_volume)
        assistant = self.audio_control_handler.create_translator(assistant)

        return Automaton(assistant, context)

    def pre_run_setup(self):
        for template in self.intents_:
            template.prepare()
        for template in self.replies_:
            template.prepare()
        self.settings.audio_api.wait_for_availability(self.settings.delay_for_ac_server)
        self.audio_control_handler.setup()
        self.settings.audio_api.set_volume(self.settings.initial_volume)


    def create_driver(self) -> kaia_core.KaiaDriver:
        command_source = ac.AudioControlCommandSource(self.settings.audio_api)

        return kaia_core.KaiaDriver(
            self.create_automaton,
            self.settings.audio_api.play_audio,
            (command_source,),
            self.settings.kaia_api,
            time_tick_frequency_in_seconds=1,
            enable_time_tick=True,
            log_file=self.settings.log_file
        )