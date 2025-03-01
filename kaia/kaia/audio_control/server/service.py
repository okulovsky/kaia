from pathlib import Path

from brainbox.framework.common.marshalling import endpoint
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

    @endpoint(url='/status', method='GET')
    def status(self):
        rows = []
        now = datetime.now()
        for m in self.cycle.responds_log:
            row = {}
            row['ago'] = (now - m.timestamp).total_seconds()
            if m.exception is not None:
                row['exception'] = m.exception
            if m.iteration_result is not None:
                row['state_b'] = m.iteration_result.mic_state_before.name
                row['state'] = m.iteration_result.mic_state_now.name
                row['play_b'] = None if m.iteration_result.playing_before is None else f'+ {m.iteration_result.playing_before.recording.title}'
                row['play'] = None if m.iteration_result.playing_now is None else f'+ {m.iteration_result.playing_now.recording.title}'
                row['input'] = m.iteration_result.produced_file_name
            rows.append(row)
        return pd.DataFrame(rows)

    @endpoint(url='/graph', method='GET')
    def graph(self):
        from matplotlib import pyplot as plt
        import base64
        df = pd.DataFrame([z.__dict__ for z in self.cycle._levels])
        fig, ax = plt.subplots(1,1,figsize=(20,10))
        df.set_index('timestamp').level.plot(ax=ax)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        bts = buf.getvalue()
        base64EncodedStr = base64.b64encode(bts).decode('ascii')
        return f'<img src="data:image/png;base64, {base64EncodedStr}"/>'

    @endpoint(url='/index', method='GET')
    def index(self):
        message_lines = []
        message_lines.append('AudioControlServer is running')
        now = datetime.now()
        message_lines.append(f'Updated {(now-self.cycle.last_update_time).total_seconds()} seconds ago')
        df = self.status()
        message_lines.append(df.to_html())
        return "<br>".join(message_lines)

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



