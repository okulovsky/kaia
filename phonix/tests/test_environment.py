from typing import Any
from phonix.daemon import (
    PhonixDeamon, FakeInput, FakeOutput,
    PorcupineWakeWordUnit, SilenceMarginUnit, TooLongOpenMicUnit,
    RecordingUnit, LevelReportingUnit, FolderFileRetriever
)
from phonix.components import PhonixApi
from dataclasses import dataclass
from avatar.messaging import TestStream, StreamClient
from avatar.server import AvatarStream
from threading import Thread
from pathlib import Path
from foundation_kaia.misc import Loc


@dataclass
class TestEnvironment:
    api: PhonixApi
    daemon: PhonixDeamon
    recording_api_test_environment: PhonixApi.Test
    client: StreamClient
    thread: Thread
    folder_holder: Any


class PhonixTestEnvironmentFactory:
    def __init__(self,
                 level_reporting: bool = False,
                 waiting_time_to_close_the_mic = 10,
                 with_recording_server: bool = False
                 ):
        self.level_reporting = level_reporting
        self.waiting_time_to_close_the_mic = waiting_time_to_close_the_mic
        self.with_recording_server = with_recording_server


    def __enter__(self):
        if self.with_recording_server:
            folder_holder = Loc.create_test_folder()
            recording_api_test = PhonixApi.Test(folder_holder.__enter__())
            api = recording_api_test.__enter__()
            getter = api.file_cache.download
            client = AvatarStream(api).create_client(None)
        else:
            folder_holder = None
            recording_api_test = None
            api = None
            getter = FolderFileRetriever(Path(__file__).parent/'files')
            client = TestStream().create_client(None)

        silence_unit = SilenceMarginUnit(0.05, 1)
        if not self.level_reporting:
            silence_unit.time_between_silence_level_reports_in_seconds = None


        units = [
            PorcupineWakeWordUnit(),
            silence_unit,
            RecordingUnit(api, 1.1),
            TooLongOpenMicUnit(self.waiting_time_to_close_the_mic),
        ]

        if self.level_reporting:
            units.append(LevelReportingUnit())

        daemon = PhonixDeamon(
            client,
            getter,
            FakeInput(),
            FakeOutput(5),
            units,
            PhonixDeamon.get_default_system_sounds()
        )
        thread = Thread(target=daemon.run, daemon=True)
        thread.start()
        self.env = TestEnvironment(
            api,
            daemon,
            recording_api_test,
            client.clone(),
            thread,
            folder_holder
        )
        return self.env

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.env.recording_api_test_environment is not None:
            self.env.recording_api_test_environment.__exit__(exc_type, exc_val, exc_tb)
        if self.env.folder_holder is not None:
            self.env.folder_holder.__exit__(exc_type, exc_val, exc_tb)
        self.env.daemon.terminate()
        self.env.thread.join()



