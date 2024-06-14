
from ..core import IAudioInput, MicData
import numpy as np

class PyAudioInput(IAudioInput):


    def __init__(self,
                 device:int = -1,
                 rate: int = 16000,
                 chunk: int = 512,
                 channels: int = 1,

                 ):
        import pyaudio
        self.FORMAT = pyaudio.paInt16
        self.pyaudio = pyaudio.PyAudio()
        self.device = device
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.stream = None


    def start(self):
        self.stream = self.pyaudio.open(
            format=self.FORMAT,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=self.device
        )

    def read(self) -> list[int]:
        buffer = self.stream.read(self.chunk)
        array = np.frombuffer(buffer, dtype='int16')
        return list(array)



    def stop(self):
        self.stream.close()
        self.stream = None


    def is_running(self) -> bool:
        return self.stream is not None

    def get_mic_data(self):
        return MicData(self.rate, self.chunk)


    @staticmethod
    def list_input_devices():
        import pyaudio
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
