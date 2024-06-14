import time
from .server import AudioControlEndpoints
from .audio_control import AudioControlData
from kaia.infra.marshalling_api import MarshallingEndpoint

class AudioControlAPI(MarshallingEndpoint.API):
    def __init__(self, address: str):
        super().__init__(address)

    def play_audio(self, audio: bytes):
        return self.caller.call(AudioControlEndpoints.play_audio, audio)

    def set_mode(self, mode: str):
        return self.caller.call(AudioControlEndpoints.set_mode,mode)

    def get_command(self) -> AudioControlData | None:
        return self.caller.call(AudioControlEndpoints.get_command)

    def wait_for_command(self, max_sleep_time_in_seconds = None):
        return self.caller.call(AudioControlEndpoints.wait_for_command, max_sleep_time_in_seconds)

    def set_paused(self, pause: bool):
        return self.caller.call(AudioControlEndpoints.set_paused, pause)

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



