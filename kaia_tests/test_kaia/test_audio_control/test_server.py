from unittest import TestCase
from kaia_tests.test_kaia.test_audio_control.setup import *
from kaia.infra import Loc
from kaia.infra.app import KaiaApp
from kaia.kaia.audio_control.wav_streaming import WavStreamingTestApi, WavApiSettings, WavServerSettings
from kaia.kaia.audio_control import AudioControlServer, AudioControlAPI, MicState
from pathlib import Path
from kaia.brainbox import BrainBoxTask
from kaia.dub import IntentsPack
from kaia.brainbox.utils import TestSpeaker
from kaia.avatar import AvatarApi, AvatarSettings, RecognitionSettings


class AudioControlServerTestCase(TestCase):
    def test_audio_control_server(self):
        with Loc.create_temp_folder('audio_control_bb_folder', dont_delete=True) as folder:
            with create_brainbox_test_api(folder) as bb_api:
                speaker = TestSpeaker(bb_api, copy_to_bb_folder=False)
                with WavStreamingTestApi(WavApiSettings(), WavServerSettings(folder)) as wav_api:
                    with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api)) as avatar_api:
                        settings = create_audio_control_settings(wav_api.settings.address)

                        settings.load_mic_samples = [
                            speaker.speak('Computer!'),
                            speaker.speak('Are you here?'),
                            speaker.speak('Computer!'),
                            speaker.speak("Repeat after me!"),
                            speaker.speak("Make me a sandwich")
                        ]

                        app = KaiaApp()
                        audio_server = AudioControlServer(settings.create_audio_control, settings.port)
                        app.add_subproc_service(audio_server)
                        audio_api = AudioControlAPI(f'127.0.0.1:{settings.port}')

                        avatar_api.recognition_train(
                            (IntentsPack('CORE', tuple(TestIntents.get_templates())),),
                            ()
                        )


                        with app.test_runner():
                            audio_api.wait_for_availability(5)
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            filename = audio_api.wait_for_uploaded_filename()
                            utterance = avatar_api.recognition_transcribe(
                                filename,
                                RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model='CORE')
                            )
                            self.assertIn(utterance, TestIntents.ping)

                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            filename = audio_api.wait_for_uploaded_filename()
                            utterance = avatar_api.recognition_transcribe(
                                filename,
                                RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model='CORE')
                            )
                            self.assertIn(utterance, TestIntents.echo)

                            audio_api.set_state(MicState.Open)
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            filename = audio_api.wait_for_uploaded_filename()
                            text = avatar_api.recognition_transcribe(
                                filename,
                                RecognitionSettings(RecognitionSettings.NLU.Whisper)
                            )
                            self.assertEqual("make me a sandwich.", text.lower())



