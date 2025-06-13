import time
from unittest import TestCase
from kaia.common import Loc
from kaia.kaia.audio_control.wav_streaming import WavStreamingApi, WavApiSettings, WavServerSettings
from pathlib import Path
from brainbox import BrainBoxTask, BrainBoxApi
from brainbox.deciders import OpenTTS, Whisper
from avatar.utils import TestSpeaker
from kaia.kaia import audio_control as ac
from yo_fluq import FileIO, Query
from kaia.tests.test_kaia.test_audio_control import create_test_settings
class FileStasher:
    def __init__(self, path: Path):
        self.path = path
        FileIO.write_text('', self.path)

    def __call__(self, fname: str):
        with open(self.path,'a') as stream:
            stream.write(fname+"\n")


class AudioControlServerTestCase(TestCase):
    def test_audio_control_server(self):
        with BrainBoxApi.Test([OpenTTS(), Whisper()], always_on_planner=True, stop_containers_at_termination=False) as bb_api:
            speaker = TestSpeaker(bb_api)

            with WavStreamingApi.Test(WavApiSettings(), WavServerSettings(bb_api.cache_folder)) as wav_api:
                with Loc.create_test_file() as tmp_file:
                    stasher = FileStasher(tmp_file)
                    settings = create_test_settings(wav_api, stasher)

                    with ac.AudioControlApi.Test(settings.create_audio_control, settings.port) as ac_api:
                        self.assertEqual(ac.MicState.Standby, ac_api.get_state())

                        #Computer
                        ac_api.playback_mic_sample(speaker.speak('Computer!').path)
                        self.assertEqual(0, Query.file.text(tmp_file).count())
                        self.assertEqual(ac.MicState.Open, ac_api.get_state())

                        #Are you here?
                        ac_api.playback_mic_sample(speaker.speak("Are you here?").path)
                        self.assertEqual(ac.MicState.Standby, ac_api.get_state())
                        files = Query.file.text(tmp_file).to_list()
                        self.assertEqual(1, len(files))

                        path_to_file = bb_api.cache_folder/files[-1]
                        self.assertTrue(path_to_file.is_file())
                        recognized = bb_api.execute(BrainBoxTask.call(Whisper).transcribe(files[-1], 'base'))
                        self.assertEqual('Are you here?', recognized)

                        ac_api.set_state(ac.MicState.Open)
                        time.sleep(0.1)
                        self.assertEqual(ac.MicState.Open, ac_api.get_state())
                        ac_api.playback_mic_sample(speaker.speak("Make me a sandwich").path)
                        self.assertEqual(ac.MicState.Standby, ac_api.get_state())

                        files = Query.file.text(tmp_file).to_list()
                        self.assertEqual(2, len(files))
                        recognized = bb_api.execute(BrainBoxTask.call(Whisper).transcribe(files[-1], 'base'))
                        self.assertEqual('Make me a sandwich.', recognized)

