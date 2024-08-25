from pvrecorder import PvRecorder
from .audio_input import IAudioInput

class PvRecorderInput(IAudioInput):
    def __init__(self,
                 device_index = -1,
                 frame_length = 512,
                 ):
        self.device_index = device_index
        self.frame_length = frame_length
        try:
            self.recoder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
        except Exception as ex:
            raise ValueError(f"Mic didn't initialize at {device_index}") from ex
        self._is_running: None | bool = None

    def get_sample_rate(self):
        return self.recoder.sample_rate

    def start(self):
        self._is_running = True
        self.recoder.start()

    def stop(self):
        self._is_running = False
        self.recoder.stop()
        #self.recoder.delete() TODO: do we need to do it

    def is_running(self) -> bool:
        return self._is_running


    def read(self):
        return self.recoder.read()





