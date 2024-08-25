from kaia.kaia.audio_control import AudioControlAPI, AudioControlCommandSource
import time
from kaia.kaia.core import KaiaDriver, KaiaGuiApi, KaiaCoreService
from kaia.kaia import skills as sk
from kaia.brainbox import BrainBoxApi
from kaia.kaia.translators import KaiaMessageTranslator, VoiceoverTranslator, AudioControlHandler
from kaia.eaglesong.core import Automaton


class KaiaTestService(KaiaCoreService):
    def __init__(self,
                 brainbox_api: BrainBoxApi,
                 audio_api: AudioControlAPI,
                 kaia_gui_api: KaiaGuiApi):
        self.brainbox_api = brainbox_api
        self.audio_api = audio_api
        self.kaia_gui_api = kaia_gui_api
        self.audio_control_handler = AudioControlHandler(audio_api, brainbox_api, kaia_gui_api, self._get_intents)
        super().__init__()

    def _get_intents(self):
        return self.create_assistant().get_intents()

    def create_assistant(self):
        skills = []
        skills.append(sk.PingSkill())
        skills.append(sk.EchoSkill())
        assistant = sk.KaiaTestAssistant(skills)
        return assistant

    def create_automaton(self, context):
        assistant = self.create_assistant()

        assistant = VoiceoverTranslator(assistant, None)
        assistant = KaiaMessageTranslator(assistant, self.kaia_gui_api)
        assistant = self.audio_control_handler.create_translator(assistant)

        return Automaton(assistant, context)

    def create_driver(self) -> KaiaDriver:
        return KaiaDriver(
            self.create_automaton,
            self.audio_api.play_audio,
            [AudioControlCommandSource(self.audio_api)],
            self.kaia_gui_api
        )

    def pre_run_setup(self):
        self.wait_for_availability()
        self.audio_control_handler.setup()


    def wait_for_availability(self):
        while not self.audio_api.check_availability():
            time.sleep(0.1)
        while not self.kaia_gui_api.check_availability():
            time.sleep(0.1)

