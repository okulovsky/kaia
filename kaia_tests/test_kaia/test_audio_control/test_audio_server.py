import time
from unittest import TestCase
from kaia.kaia.audio_control.core import AudioControlServer, AudioControlAPI
from kaia_tests.test_kaia.test_audio_control.audio_control_cycle import create_audio_control_settings, get_intents
from kaia.infra.app import KaiaApp
from pathlib import Path

class AudioControlServerTestCase(TestCase):
    def test_audio_server(self):
        settings = create_audio_control_settings()

        settings.load_mic_samples = [
            Path(__file__).parent / 'files/computer.wav',
            Path(__file__).parent / 'files/are_you_here.wav',
            Path(__file__).parent / 'files/computer.wav',
            Path(__file__).parent / 'files/repeat_after_me.wav'
        ]
        settings.rhasspy_api.setup_intents(get_intents())
        settings.rhasspy_api.train()
        app = KaiaApp()
        audio_server = AudioControlServer(settings.create_audio_control, settings.port)
        app.add_subproc_service(audio_server)
        audio_api = AudioControlAPI(f'127.0.0.1:{settings.port}')

        with app.test_runner():
            audio_api.wait_for_availability(5)
            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            if not audio_api.is_alive():
                raise ValueError('Server is dead')
            self.assertEqual('ping', audio_api.wait_for_command(3).payload['intent']['name'])
            self.assertIsNone(audio_api.get_command())

            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            audio_api.next_mic_sample()
            audio_api.wait_for_mic_sample_to_finish()
            if not audio_api.is_alive():
                raise ValueError('Server is dead')
            self.assertEqual('echo', audio_api.wait_for_command(3).payload['intent']['name'])
            self.assertIsNone(audio_api.get_command())




