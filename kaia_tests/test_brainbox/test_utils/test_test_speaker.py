import os
from unittest import TestCase
from kaia.brainbox.utils import TestSpeaker
from kaia.brainbox.deciders import OpenTTSInstaller, OpenTTSSettings
from kaia.brainbox import BrainBoxApi

class TestSpeakerTestCase(TestCase):
    def test_test_speaker(self):
        test_sentence = 'Hello, world!'
        with BrainBoxApi.Test(dict(OpenTTS = OpenTTSInstaller(OpenTTSSettings()))) as api:
            speaker = TestSpeaker(api)
            filename = speaker.get_path(test_sentence)
            self.assertEqual("p256___Hello_world.wav", filename.name)

            if filename.is_file():
                os.unlink(filename)
            self.assertFalse(filename.is_file())

            voiceover_1 = speaker.speak(test_sentence)
            self.assertTrue((api.cache_folder/voiceover_1).is_file())
            self.assertTrue(filename.is_file())

            with open(filename,'wb') as file:
                file.write(b'123')

            voiceover_2 = speaker.speak(test_sentence)
            self.assertNotEquals(voiceover_2, voiceover_1)
            self.assertTrue((api.cache_folder/voiceover_2).is_file())

            with open(api.cache_folder/voiceover_2, 'rb') as file:
                result = file.read()
                self.assertEquals(b'123', result)




