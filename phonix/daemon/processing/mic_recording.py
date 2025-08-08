from .core import IUnit, State, UnitInput
from avatar.server.components.audio_chunks import WavWriter
import atexit


class MicRecordingUnit(IUnit):
    def __init__(self, file_name):
        self.file_name = file_name
        self.stream = None
        self.wav_file = None
        self.current_sample_rate = None
        self.index = 0
        atexit.register(self.exiting)

    def exiting(self):
        if self.wav_file is not None:
            self.wav_file.close()

    def open_file(self, sample_rate):
        if self.current_sample_rate is None or sample_rate != self.current_sample_rate:
            if self.wav_file is not None:
                self.wav_file.close()

            fname = str(self.file_name).replace('.wav', f'-{self.index}.wav')
            self.index+=1
            self.stream = open(fname, 'wb')
            self.wav_file = WavWriter(self.stream, sample_rate)
            self.current_sample_rate = sample_rate


    def process(self, incoming_data: UnitInput) -> State|None:
        self.open_file(incoming_data.mic_data.sample_rate)
        self.wav_file.write_raw(incoming_data.mic_data.buffer)
        return None

