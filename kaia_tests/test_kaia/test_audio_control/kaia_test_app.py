from kaia.kaia.audio_control import AudioControlAPI, AudioControlCommandSource
import time
from kaia.kaia.core import KaiaDriver, KaiaGuiApi, KaiaAssistant, KaiaMessage
from kaia.kaia import skills as sk
from kaia.brainbox import BrainBoxApi
from kaia.kaia.translators import KaiaMessageTranslator, VoiceoverTranslator, RecognitionTranslator, OpenMicTranslator
from kaia.eaglesong.core import Automaton
from kaia.avatar import AvatarApi
from kaia.kaia.audio_control_core_service import KaiaCoreAudioControlService, KaiaCoreAudioControlServiceSettings

class KaiaTestService(KaiaCoreAudioControlService):
    def __init__(self, settings: KaiaCoreAudioControlServiceSettings):
        super().__init__(settings)


    def create_assistant(self):
        skills = []
        skills.append(sk.PingSkill())
        skills.append(sk.EchoSkill())
        assistant = KaiaAssistant(skills)
        return assistant


    def create_driver(self) -> KaiaDriver:
        #Overriden to ease some of the base class settings
        return KaiaDriver(
            self.create_automaton,
            self.settings.audio_api.play_audio,
            [AudioControlCommandSource(self.settings.audio_api)],
            self.settings.kaia_api
        )

    def create_automaton(self, context):
        assistant = self.create_assistant()
        #assistant = VoiceoverTranslator(assistant, self.settings.avatar_api)
        assistant = KaiaMessageTranslator(assistant, self.settings.kaia_api, self.settings.avatar_api, self.settings.name_to_avatar_image)
        assistant = RecognitionTranslator(assistant, self.settings.avatar_api)
        assistant = OpenMicTranslator(assistant, self.settings.audio_api)

        return Automaton(assistant, context)


    def wait_for_availability(self):
        while not self.settings.audio_api.check_availability():
            time.sleep(0.1)
        while not self.settings.kaia_api.check_availability():
            time.sleep(0.1)

