from unittest import TestCase
from kaia.brainbox.deciders.docker_based import RhasspyInstaller, RhasspySettings
from kaia_tests.test_kaia.test_audio_control.audio_control_cycle import get_intents
from kaia.avatar.dub.core import RhasspyAPI
from pathlib import Path

class RecognitionTestCase(TestCase):
    def test_rhasspy(self):
        rhasspy_installer = RhasspyInstaller(RhasspySettings())
        rhasspy_installer.install_if_not_installed()
        rhasspy_installer.server_endpoint.run()
        rhasspy_api = RhasspyAPI('127.0.0.1:12101', get_intents())
        rhasspy_api.train()
        self.assertEqual('ping', rhasspy_api.recognize(Path(__file__).parent/'files/are_you_here.wav').template.name)
        self.assertEqual('echo', rhasspy_api.recognize(Path(__file__).parent/'files/repeat_after_me.wav').template.name)
