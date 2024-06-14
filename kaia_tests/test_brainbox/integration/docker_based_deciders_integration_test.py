from typing import *
from unittest import TestCase
from kaia.brainbox.core import IInstaller

class DockerBasedDecidersIntegrationTestCase(TestCase):

    def run_test(self: TestCase, settings, installer_factory: Callable[[Any], IInstaller]):
        installer = installer_factory(settings)
        if installer.is_installed():
            installer.uninstall()
        self.assertFalse(installer.is_installed())
        installer.install()
        self.assertTrue(installer.is_installed())
        installer.self_test(self)

    def test_coqui_tts(self):
        from kaia.brainbox.deciders.docker_based.coqui_tts import CoquiTTSSettings, CoquiTTSInstaller
        self.run_test(CoquiTTSSettings(), CoquiTTSInstaller)

    def test_whisper(self):
        from kaia.brainbox.deciders.docker_based.whisper import WhisperSettings, WhisperInstaller
        self.run_test(WhisperSettings(), WhisperInstaller)

    def test_open_tts(self):
        from kaia.brainbox.deciders.docker_based.open_tts import OpenTTSInstaller, OpenTTSSettings
        self.run_test(OpenTTSSettings(), OpenTTSInstaller)

    def test_rhasspy(self):
        from kaia.brainbox.deciders.docker_based.rhasspy import RhasspySettings, RhasspyInstaller
        self.run_test(RhasspySettings(), RhasspyInstaller)

    def test_tortoise_tts(self):
        from kaia.brainbox.deciders.docker_based.tortoise_tts import TortoiseTTSSettings, TortoiseTTSInstaller
        self.run_test(TortoiseTTSSettings(), TortoiseTTSInstaller)

    def test_snips_nlu(self):
        from kaia.brainbox.deciders.docker_based import SnipsNLUSettings, SnipsNLUInstaller
        self.run_test(SnipsNLUSettings(), SnipsNLUInstaller)

