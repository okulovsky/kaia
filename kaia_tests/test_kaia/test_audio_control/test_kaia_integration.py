import time
from unittest import TestCase

import requests

from kaia.kaia.audio_control.core import AudioControlServer, AudioControlAPI, AudioControlCommandSource
from kaia.kaia.translators import AudioControlListenTranslator
from kaia_tests.test_kaia.test_audio_control.audio_control_cycle import create_audio_control_settings
from kaia.infra.app import KaiaApp
from kaia.kaia.core import KaiaGuiService, KaiaDriver, KaiaGuiApi, KaiaCoreService, RhasspyDriverSetup
from kaia.kaia import skills as sk
from pathlib import Path
from kaia.avatar.dub.core import RhasspyAPI
from kaia.kaia.translators import UtterancesPresenter, VoiceoverTranslator, AudioControlInputTranslator
from kaia.eaglesong.core import Automaton
from pprint import pprint

def automaton_factory(context):
    pass

class KaiaTestService(KaiaCoreService):
    def __init__(self,
                 rhasspy_api: RhasspyAPI,
                 audio_api: AudioControlAPI,
                 kaia_api: KaiaGuiApi):
        self.rhasspy_api = rhasspy_api
        self.audio_api = audio_api
        self.kaia_api = kaia_api
        super().__init__()

    def create_assistant(self):
        skills = []
        skills.append(sk.PingSkill())
        skills.append(sk.EchoSkill())
        assistant = sk.KaiaTestAssistant(skills)
        return assistant

    def create_automaton(self, context):
        assistant = self.create_assistant()
        assistant = AudioControlListenTranslator(assistant, self.audio_api,'whisper')
        assistant = VoiceoverTranslator(assistant, None)
        assistant = UtterancesPresenter(assistant, self.kaia_api)
        assistant = AudioControlInputTranslator(assistant, self.rhasspy_api)

        return Automaton(assistant, context)

    def create_driver(self) -> KaiaDriver:
        return KaiaDriver(
            self.create_automaton,
            self.audio_api.play_audio,
            [AudioControlCommandSource(self.audio_api)],
            self.kaia_api
        )

    def pre_run_setup(self):
        self.wait_for_availability()
        RhasspyDriverSetup(self.rhasspy_api, self.kaia_api)(self)



    def wait_for_availability(self):
        while not self.audio_api.check_availability():
            time.sleep(0.1)
        while not self.kaia_api.check_availability():
            time.sleep(0.1)



class KaiaIntegrationTestCase(TestCase):
    def test_integration(self):
        app = KaiaApp()
        settings = create_audio_control_settings()
        settings.load_mic_samples = [
            Path(__file__).parent/'files/computer.wav',
            Path(__file__).parent/'files/are_you_here.wav',
            Path(__file__).parent/'files/computer.wav',
            Path(__file__).parent/'files/repeat_after_me.wav',
            Path(__file__).parent/'files/random_text_outside_of_intents.wav'
        ]
        settings.pause_between_iterations_in_seconds=0.01
        audio_server = AudioControlServer(settings.create_audio_control, settings.port)
        app.add_subproc_service(audio_server)
        kaia_server = KaiaGuiService()
        app.add_subproc_service(kaia_server)
        audio_api = AudioControlAPI(f'127.0.0.1:{settings.port}')
        kaia_api = KaiaGuiApi(f'127.0.0.1:{kaia_server._port}')
        core_server = KaiaTestService(settings.rhasspy_api, audio_api, kaia_api)
        app.add_subproc_service(core_server)

        intents_list = core_server.create_assistant().get_intents()
        settings.rhasspy_api.setup_intents(intents_list)
        settings.rhasspy_api.train()

        with app.test_runner():
            core_server.wait_for_availability()

            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()

            self.assertEqual(4, len(kaia_api.updates()['chat']))

            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()

            self.assertEqual(6, len(kaia_api.updates()['chat']))

            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()

            self.assertEqual(8, len(kaia_api.updates()['chat']))
            pprint(kaia_api.updates()['chat'])

