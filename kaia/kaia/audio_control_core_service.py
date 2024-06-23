from kaia.kaia import core as kaia_core
from kaia.kaia import translators as kaia_translators
from kaia.kaia import audio_control as ac
from kaia.kaia.skills.change_image_skill import ChangeImageIntents
from kaia.kaia.skills.character_skill import ChangeCharacterIntents

from kaia.avatar.server import AvatarAPI
from kaia.avatar.dub.core import RhasspyAPI
from pathlib import Path
from kaia.eaglesong.core import Automaton
from dataclasses import dataclass



@dataclass
class KaiaCoreAudioControlServiceSettings:
    avatar_api: AvatarAPI
    rhasspy_api: RhasspyAPI
    kaia_api: kaia_core.KaiaGuiApi
    audio_api: ac.AudioControlAPI
    initial_volume: float = 0.1
    delay_for_ac_server: int = 10
    log_file: Path|None = None


class KaiaCoreAudioControlService(kaia_core.KaiaCoreService):
    def __init__(self,
                 settings: KaiaCoreAudioControlServiceSettings
                 ):
        self.settings = settings

    def create_automaton(self, context):
        assistant = self.create_assistant()

        assistant = kaia_translators.InitializationWrap(
            assistant,
            [ChangeImageIntents.change_image.utter()],
            [ChangeCharacterIntents.change_character.utter()],
            False
        )

        assistant = kaia_translators.VoiceoverTranslator(assistant, self.settings.avatar_api)
        assistant = kaia_translators.UtterancesPresenter(assistant, self.settings.kaia_api)
        assistant = kaia_translators.VolumeTranslator(assistant, self.settings.audio_api.set_volume, self.settings.initial_volume)
        assistant = kaia_translators.AudioControlInputTranslator(assistant, self.settings.rhasspy_api)
        assistant = kaia_translators.AudioControlListenTranslator(assistant, self.settings.audio_api, 'whisper')

        return Automaton(assistant, context)

    def pre_run_setup(self):
        self.settings.audio_api.wait_for_availability(self.settings.delay_for_ac_server)
        kaia_core.RhasspyDriverSetup(self.settings.rhasspy_api, self.settings.kaia_api, True, None)(self)
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