from pathlib import Path

from foundation_kaia.marshalling import endpoint
import time
from typing import *
import pandas as pd
from ..audio_control_cycle import AudioControlCycle, MicState
from ..outputs import Recording, RecordingInstance
from ..inputs import FakeInput
from threading import Thread
from datetime import datetime
import io
from .interface import IAudioControlApi

class AudioControlService(IAudioControlApi):
    def __init__(self, cycle_factory: Callable[[], AudioControlCycle]):
        self.cycle_factory = cycle_factory
        self.cycle: Optional[AudioControlCycle] = None


    def start(self):
        self.cycle = self.cycle_factory()
        Thread(target=self.cycle.run, daemon=True).start()

    @endpoint(url='/is_alive', method='GET')
    def is_alive(self):
        now = self.cycle.last_update_time
        while True:
            if (datetime.now() - now).total_seconds() > 1:
                return False
            if self.cycle.last_update_time != now:
                return True
            time.sleep(0.01)

    @endpoint(url='/play_audio')
    def play_audio(self, audio: bytes):
        content = RecordingInstance(Recording(audio), False)
        self.cycle.request_recording(content)
        while content.state != RecordingInstance.State.Finished:
            time.sleep(0.1)

    @endpoint(url='/set_state')
    def set_state(self, state: MicState):
        start = datetime.now()
        self.cycle.request_state(state)
        while True:
            if self.cycle.get_state() == state:
                return
            if (datetime.now() - start).total_seconds() > 1:
                raise ValueError("Could not wait until the state changes")

    @endpoint(url='/get_state', method='GET')
    def get_state(self):
        return self.cycle.get_state()


    @endpoint(url='/get_uploaded_filename', method='GET')
    def get_uploaded_filename(self) -> str|None:
        return self.cycle.get_produced_file()

    @endpoint(url='/wait_for_uploaded_filename', method="GET")
    def wait_for_uploaded_filename(self, max_sleep_time_in_seconds = None) -> str:
        return self.cycle.get_produced_file(True, max_sleep_time_in_seconds)

    @endpoint(url='/set_mic_sample', method='POST')
    def set_mic_sample(self, sample: Path):
        if not isinstance(self.cycle._drivers.input, FakeInput):
            raise ValueError("MicSample can only be requested for FakeInput")
        self.cycle._drivers.input.set_sample(sample)


    @endpoint(url='/is_mic_sample_finished', method='GET')
    def is_mic_sample_finished(self):
        if not isinstance(self.cycle._drivers.input, FakeInput):
            return
        return self.cycle._drivers.input.is_buffer_empty()

    @endpoint(url='/set_volumn', method='POST')
    def set_volume(self, volume: float):
        self.cycle._drivers.output.set_volume(volume)



