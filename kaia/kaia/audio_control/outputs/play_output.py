from .audio_output import IAudioOutput, RecordingInstance

from threading import Thread
from .play_server import PlayApi
from queue import Queue

class RequestPolling:
    def __init__(self, api, content):
        self.api = api
        self.content = content
        self.finished = False

    def start(self):
        thread = Thread(target=self._internal)
        thread.start()

    def _internal(self):
        result = self.api.play(self.content)
        self.finished = True

    def is_alive(self):
        return not self.finished



class PlayOutput(IAudioOutput):
    def __init__(self, address: str):
        self.api = PlayApi(address)
        self.current_sample: RecordingInstance | None = None
        self.polling: RequestPolling | None = None

    def start_playing(self, sample: RecordingInstance):
        if self.polling is not None:
            raise ValueError("Must wait until previous sample played")
        self.polling = RequestPolling(self.api, sample.recording.content)
        self.polling.start()
        self.current_sample = sample

    def what_is_playing(self) -> RecordingInstance|None:
        if self.polling is None:
            return None
        if self.polling.is_alive():
            return self.current_sample
        self.polling = None
        self.current_sample = None

    def set_volume(self, volume: float):
        self.api.volume(volume)

