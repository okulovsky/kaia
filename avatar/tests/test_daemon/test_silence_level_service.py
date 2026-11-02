from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from avatar.daemon import SilenceLevelService
from avatar.daemon.common import InitializationEvent, SoundLevelReport


class SilenceLevelServiceTestCase(TestCase):
    def test_default_level_survives_restart(self):
        with TemporaryDirectory() as folder:
            for _ in range(2):
                service = SilenceLevelService(default_silence_level=0.2)
                service.set_resources_folder(Path(folder))
                self.assertEqual(0.2, service.on_initialization(InitializationEvent()).level)

    def test_changed_level_survives_restart(self):
        with TemporaryDirectory() as folder:
            service = SilenceLevelService()
            service.set_resources_folder(Path(folder))
            service.on_initialization(InitializationEvent())
            service.on_changed_level(SoundLevelReport(None, 0.3, datetime.now(), datetime.now(), []))
            restarted = SilenceLevelService()
            restarted.set_resources_folder(Path(folder))
            self.assertEqual(0.3, restarted.on_initialization(InitializationEvent()).level)
