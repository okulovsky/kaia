import time
from typing import *

import pandas as pd

from kaia.infra.marshalling_api import MarshallingEndpoint
from .audio_control import AudioControl
from .dto import AudioSampleTemplate, AudioSample
from .fake_input import FakeInput
import flask
from threading import Thread
from datetime import datetime

class AudioControlEndpoints:
    play_audio = MarshallingEndpoint('/play_audio')
    set_mode = MarshallingEndpoint('/set_mode')
    get_command = MarshallingEndpoint('/get_command', 'GET')
    wait_for_command = MarshallingEndpoint('/wait_for_command', 'GET')
    set_paused = MarshallingEndpoint('/set_paused')
    next_mic_sample = MarshallingEndpoint('/debug/next_mic_sample')
    is_mic_sample_finished = MarshallingEndpoint('/debug/is_sample_finished')
    set_volume = MarshallingEndpoint('/set_volume')
    is_alive = MarshallingEndpoint('/is_alive')


class AudioControlServer:
    def __init__(self,
                 cycle_factory: Callable[[], AudioControl],
                 port: int
                 ):
        self.port = port
        self.cycle_factory = cycle_factory
        self.cycle: Optional[AudioControl] = None

    def __call__(self):
        self.cycle = self.cycle_factory()
        Thread(target=self.cycle.run, daemon=True).start()
        self.app = flask.Flask('avatar')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(AudioControlEndpoints, self)
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.run('0.0.0.0', self.port)


    def index(self):
        message_lines = []
        message_lines.append('AudioControlServer is running')
        now = datetime.now()
        message_lines.append(f'Updated {(now-self.cycle.last_update_time).total_seconds()} seconds ago')
        rows = []
        for m in self.cycle.responds_log:
            row = {}
            row['ago'] = (now - m.timestamp).total_seconds()
            if m.exception is not None:
                row['exception'] = m.exception
            if m.iteration_result is not None:
                row['from'] = m.iteration_result.from_state
                row['to'] = m.iteration_result.to_state
                row['started'] = None if m.iteration_result.audio_sample_started is None else f'+ {m.iteration_result.audio_sample_started.template.title}'
                row['finished'] = None if m.iteration_result.audio_sample_finished is None else f'+ {m.iteration_result.audio_sample_finished.template.title}'
                row['input'] = m.iteration_result.processed_input is not None
            rows.append(row)
        message_lines.append(pd.DataFrame(rows).to_html())
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
        content = AudioSample(AudioSampleTemplate(audio), False)
        self.cycle.play_requests_queue.put(content)
        while content.state != AudioSample.State.Finished:
            time.sleep(0.1)

    def set_mode(self, mode: str):
        self.cycle.states_requests_queue.put(mode)


    def get_command(self):
        if self.cycle.commands_queue.empty():
            return None
        cmd = self.cycle.commands_queue.get()
        return cmd

    def wait_for_command(self, max_sleep_time_in_seconds = None):
        begin = datetime.now()
        while self.cycle.commands_queue.empty():
            time.sleep(0.1)
            if max_sleep_time_in_seconds is not None:
                if (datetime.now() - begin).total_seconds() > max_sleep_time_in_seconds:
                    raise ValueError(f"Coulnd't get the command within {max_sleep_time_in_seconds}")
        cmd = self.cycle.commands_queue.get()
        return cmd

    def set_paused(self, pause: bool):
        self.cycle.set_paused(pause)

    def next_mic_sample(self):
        if not isinstance(self.cycle.input, FakeInput):
            return
        self.cycle.input.next_buffer()
        return self.cycle.input.current_buffer

    def is_mic_sample_finished(self):
        if not isinstance(self.cycle.input, FakeInput):
            return
        return self.cycle.input.is_buffer_empty()

    def set_volume(self, volume: float):
        self.cycle.output.set_volume(volume)



