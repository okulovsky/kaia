from unittest import TestCase
from kaia_tests.test_kaia.test_audio_control.setup import *
from kaia.infra import Loc
from kaia.infra.app import KaiaApp
from kaia.kaia.audio_control.wav_streaming import WavStreamingTestApi, WavApiSettings, WavServerSettings
from kaia.kaia.audio_control import AudioControlServer, AudioControlAPI, MicState
from pathlib import Path
from kaia.kaia.translators import AudioControlHandler
from kaia.brainbox import BrainBoxTask


class AudioControlServerTestCase(TestCase):
    def test_audio_control_server(self):
        with Loc.create_temp_folder('audio_control_bb_folder', dont_delete=True) as folder:
            with create_brainbox_test_api(folder) as bb_api:
                with WavStreamingTestApi(WavApiSettings(), WavServerSettings(folder)) as wav_api:
                    settings = create_audio_control_settings(wav_api.settings.address)

                    settings.load_mic_samples = [
                        Path(__file__).parent / 'files/computer.wav',
                        Path(__file__).parent / 'files/are_you_here.wav',
                        Path(__file__).parent / 'files/computer.wav',
                        Path(__file__).parent / 'files/repeat_after_me.wav',
                        Path(__file__).parent/'files/make_me_a_sandwich.wav'
                    ]


                    app = KaiaApp()
                    audio_server = AudioControlServer(settings.create_audio_control, settings.port)
                    app.add_subproc_service(audio_server)
                    audio_api = AudioControlAPI(f'127.0.0.1:{settings.port}')

                    handler = AudioControlHandler(audio_api, bb_api, None, TestIntents.get_templates)
                    handler.setup()

                    with app.test_runner():
                        audio_api.wait_for_availability(5)
                        audio_api.next_mic_sample()
                        audio_api.wait_for_mic_sample_to_finish()
                        audio_api.next_mic_sample()
                        audio_api.wait_for_mic_sample_to_finish()
                        filename = audio_api.wait_for_uploaded_filename()
                        utterance = handler.run_rhasspy_recognition(filename)
                        self.assertIn(utterance, TestIntents.ping)

                        audio_api.next_mic_sample()
                        audio_api.wait_for_mic_sample_to_finish()
                        audio_api.next_mic_sample()
                        audio_api.wait_for_mic_sample_to_finish()
                        filename = audio_api.wait_for_uploaded_filename()
                        utterance = handler.run_rhasspy_recognition(filename)
                        self.assertIn(utterance, TestIntents.echo)

                        audio_api.set_state(MicState.Open)
                        audio_api.next_mic_sample()
                        audio_api.wait_for_mic_sample_to_finish()
                        filename = audio_api.wait_for_uploaded_filename()
                        text = handler.run_whisper_recognition(filename)
                        self.assertEqual("make me a sandwich.", text.lower())



