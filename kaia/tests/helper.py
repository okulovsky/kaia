from kaia.app import KaiaApp, KaiaAppSettings
from avatar.daemon import *
from phonix.daemon import SoundLevelReport, SilenceLevelReport, SystemSoundCommand, MicStateChangeReport
from yo_fluq import Query, FileIO
from datetime import datetime
from pathlib import Path
from unittest import TestCase
from avatar.utils import slice
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumDriver:
    def __init__(self, api, headless: bool = True):
        self.api = api
        self.headless = headless

    def __enter__(self):
        opts = Options()
        if self.headless:
            opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=opts)
        driver.get(f'http://{self.api.address}/main')
        self.driver = driver
        return driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


class Helper:
    def __init__(self, folder, tc: TestCase, recompile_ts: bool = False, brainless: bool = False):
        settings = KaiaAppSettings()

        if brainless:
            settings.brainbox = None
            settings.phonix = None
            settings.avatar_processor.timer_event_span_in_seconds = None
        else:
            settings.brainbox.deciders_files_in_kaia_working_folder = False
            settings.avatar_processor.timer_event_span_in_seconds = None
            settings.avatar_processor.initialization_event_at_startup = False
            settings.avatar_server.compile_scripts = recompile_ts
            settings.phonix.in_unit_test_environment = True
            settings.phonix.supress_reports = True
            settings.brainbox.deciders_files_in_kaia_working_folder = False

        self.settings = settings
        self.app = settings.create_app(folder)
        self.tc = tc
        self.client = self.app.create_avatar_client()



    def upload(self, name):
        return self.app.avatar_api.file_cache.upload(FileIO.read_bytes(Path(__file__).parent / 'test_app/files' / (name + '.wav')))

    def process(self, q):
        def _():
            for m in q:
                if isinstance(m, ExceptionEvent):
                    print(m.source)
                    print(m.traceback)
                    exit(1)
                if isinstance(m, (SoundLevelReport, SilenceLevelReport)):
                    continue
                yield m

        return Query.en(_())

    def init(self):
        self.client.initialize()
        self.client.put(TickEvent(datetime.now()))
        kaldi_training = (
            self.client
            .query(5)
            .feed(self.process)
            .feed(slice(lambda z: isinstance(z, BrainBoxService.Confirmation)))
        )

        self.tc.assertEqual(4, len(kaldi_training))
        self.tc.assertIsInstance(kaldi_training[0], TickEvent)
        self.tc.assertIsInstance(kaldi_training[1], STTService.RhasspyTrainingCommand)
        self.tc.assertIsInstance(kaldi_training[2], BrainBoxService.Command)
        self.tc.assertIsInstance(kaldi_training[3], BrainBoxService.Confirmation)

    def say(self, file):
        self.client.put(SoundInjectionCommand(self.upload(file)))
        return self.client

    def wakeword(self):
        self.say('computer')
        msg = self.client.pull(1)[0]
        wakeup = self.client.query(5).feed(self.process).feed(slice(lambda z: isinstance(z, MicStateChangeReport), 2))

        self.tc.assertEqual(5, len(wakeup))
        self.tc.assertIsInstance(wakeup[0], WakeWordEvent)
        self.tc.assertIsInstance(wakeup[1], SystemSoundCommand)
        self.tc.assertIsInstance(wakeup[2], MicStateChangeReport)
        self.tc.assertIsInstance(wakeup[3], Confirmation)
        self.tc.assertIsInstance(wakeup[4], MicStateChangeReport)

    def parse_reaction(self, expected_command: Type):
        response = []
        msg = None
        for message in self.client.query(10).feed(self.process):
            response.append(message)
            if isinstance(message, expected_command):
                if msg is None:
                    msg = message
                else:
                    raise ValueError("Only one message is expected")
            if msg is not None:
                if message.is_confirmation_of(msg):
                    break
        return response







