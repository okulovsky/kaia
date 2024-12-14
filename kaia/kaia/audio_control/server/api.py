import time

import pandas as pd

from .server import AudioControlEndpoints
from ..audio_control_cycle import MicState
from kaia.infra.marshalling_api import MarshallingEndpoint

class AudioControlAPI(MarshallingEndpoint.API):
    def __init__(self, address: str):
        super().__init__(address)

    def status(self) -> pd.DataFrame:
        return self.caller.call(AudioControlEndpoints.status)

    def play_audio(self, audio: bytes):
        return self.caller.call(AudioControlEndpoints.play_audio, audio)

    def set_state(self, state: MicState):
        return self.caller.call(AudioControlEndpoints.set_state, state)

    def get_state(self):
        return self.caller.call(AudioControlEndpoints.get_state)

    def get_uploaded_filename(self) -> str | None:
        return self.caller.call(AudioControlEndpoints.get_uploaded_filename)

    def wait_for_uploaded_filename(self, max_sleep_time_in_seconds = None):
        return self.caller.call(AudioControlEndpoints.wait_for_uploaded_filename, max_sleep_time_in_seconds)

    def next_mic_sample(self):
        return self.caller.call(AudioControlEndpoints.next_mic_sample)

    def is_mic_sample_finished(self) -> bool:
        return self.caller.call(AudioControlEndpoints.is_mic_sample_finished)

    def is_alive(self) -> bool:
        return self.caller.call(AudioControlEndpoints.is_alive)

    def wait_for_mic_sample_to_finish(self):
        while not self.is_mic_sample_finished():
            time.sleep(0.01)

    def set_volume(self, volume: float):
        return self.caller.call(AudioControlEndpoints.set_volume, volume)



