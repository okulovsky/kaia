from typing import *
from unittest import TestCase
from kaia.brainbox.core import IInstaller
import os
from kaia.infra import FileIO, Loc


UNINSTALL = False
PURGE = False
DONT_TEST = False



class InstallAndTestCase(TestCase):
    def run_test(
            self: TestCase,
            settings,
            installer_factory: Callable[[Any], IInstaller],
            uninstall=False,
            purge = False,
            dont_test = False
    ):
        output = Loc.data_folder / 'brainbox_integration_tests'
        os.makedirs(output, exist_ok=True)

        installer = installer_factory(settings)
        if not (DONT_TEST or dont_test):
            if (output/installer.python_name).is_file():
                os.unlink(output/installer.python_name)

        if uninstall or UNINSTALL:
            if installer.is_installed():
                installer.uninstall(purge or PURGE)
                self.assertFalse(installer.is_installed())
            installer.install()
        else:
            if not installer.is_installed():
                installer.install()

        self.assertTrue(installer.is_installed())

        if not (DONT_TEST or dont_test):
            result = installer.brainbox_self_test(self)
            FileIO.write_pickle(result, output/installer.python_name)

    def test_comfyui(self):
        from kaia.brainbox.deciders.comfyui import ComfyUIInstaller, ComfyUISettings
        self.run_test(ComfyUISettings(), ComfyUIInstaller)

    def test_coqui_tts(self):
        from kaia.brainbox.deciders.coqui_tts import CoquiTTSSettings, CoquiTTSInstaller
        self.run_test(CoquiTTSSettings(), CoquiTTSInstaller)

    def test_kohya_ss(self):
        from kaia.ml.lora.brainbox_deciders.kohya_ss import KohyaSSSettings, KohyaSSInstaller
        self.run_test(KohyaSSSettings(), KohyaSSInstaller)


    def test_ollama(self):
        from kaia.brainbox.deciders import OllamaSettings, OllamaInstaller
        self.run_test(OllamaSettings(), OllamaInstaller)

    def test_open_tts(self):
        from kaia.brainbox.deciders import OpenTTSInstaller, OpenTTSSettings
        self.run_test(OpenTTSSettings(), OpenTTSInstaller)

    def test_resemblyzer(self):
        from kaia.brainbox.deciders import ResemblyzerSettings, ResemblyzerInstaller
        self.run_test(ResemblyzerSettings(), ResemblyzerInstaller)


    def test_rhasspy_kaldi(self):
        from kaia.brainbox.deciders import RhasspyKaldiSettings, RhasspyKaldiInstaller
        self.run_test(RhasspyKaldiSettings(), RhasspyKaldiInstaller, True, True)

    def test_tortoise_tts(self):
        from kaia.brainbox.deciders import TortoiseTTSSettings, TortoiseTTSInstaller
        self.run_test(TortoiseTTSSettings(), TortoiseTTSInstaller, dont_test=False)


    def test_wd14_tagger(self):
        from kaia.ml.lora.brainbox_deciders.wd14_tagger import WD14TaggerSettings, WD14TaggerInstaller
        self.run_test(WD14TaggerSettings(), WD14TaggerInstaller)

    def test_whisper(self):
        from kaia.brainbox.deciders import WhisperSettings, WhisperInstaller
        self.run_test(WhisperSettings(), WhisperInstaller)




