import time
from typing import *

import pandas as pd


from kaia.infra.marshalling_api import MarshallingEndpoint
from ..audio_control_cycle import AudioControlCycle, MicState
from ..outputs import Recording, RecordingInstance
from ..inputs import FakeInput
import flask
from threading import Thread
from datetime import datetime
import io

class AudioControlEndpoints:
    status = MarshallingEndpoint('/status')
    play_audio = MarshallingEndpoint('/play_audio')
    set_state = MarshallingEndpoint('/set_mode')
    get_state = MarshallingEndpoint('/get_state')
    get_uploaded_filename = MarshallingEndpoint('/get_command', 'GET')
    wait_for_uploaded_filename = MarshallingEndpoint('/wait_for_command', 'GET')
    next_mic_sample = MarshallingEndpoint('/debug/next_mic_sample')
    is_mic_sample_finished = MarshallingEndpoint('/debug/is_sample_finished')
    set_volume = MarshallingEndpoint('/set_volume')
    is_alive = MarshallingEndpoint('/is_alive')


class AudioControlServer:
    def __init__(self,
                 cycle_factory: Callable[[], AudioControlCycle],
                 port: int
                 ):
        self.port = port
        self.cycle_factory = cycle_factory
        self.cycle: Optional[AudioControlCycle] = None

    def __call__(self):
        self.cycle = self.cycle_factory()
        Thread(target=self.cycle.run, daemon=True).start()
        self.app = flask.Flask('audio_control')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/graph', view_func=self.graph, methods=['GET'])

        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(AudioControlEndpoints, self)

        self.app.run('0.0.0.0', self.port)

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




    def index(self):
        message_lines = []
        message_lines.append('AudioControlServer is running')
        now = datetime.now()
        message_lines.append(f'Updated {(now-self.cycle.last_update_time).total_seconds()} seconds ago')
        df = self.status()
        message_lines.append(df.to_html())
        return "<br>".join(message_lines)

    def is_alive(self):
        now = self.cycle.last_update_time
        while True:
            if (datetime.now() - now).total_seconds() > 1:
                return False
            if self.cycle.last_update_time != now:
                return True
            time.sleep(0.01)

    def play_audio(self, audio: bytes):
        content = RecordingInstance(Recording(audio), False)
        self.cycle.request_recording(content)
        while content.state != RecordingInstance.State.Finished:
            time.sleep(0.1)

    def set_state(self, state: MicState):
        self.cycle.request_state(state)

    def get_state(self):
        return self.cycle.get_state()


    def get_uploaded_filename(self) -> str|None:
        return self.cycle.get_produced_file()

    def wait_for_uploaded_filename(self, max_sleep_time_in_seconds = None) -> str:
        return self.cycle.get_produced_file(True, max_sleep_time_in_seconds)

    def next_mic_sample(self):
        if not isinstance(self.cycle._drivers.input, FakeInput):
            return
        self.cycle._drivers.input.next_buffer()
        return self.cycle._drivers.input.current_buffer

    def is_mic_sample_finished(self):
        if not isinstance(self.cycle._drivers.input, FakeInput):
            return
        return self.cycle._drivers.input.is_buffer_empty()

    def set_volume(self, volume: float):
        self.cycle._drivers.output.set_volume(volume)



