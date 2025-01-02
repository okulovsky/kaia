import time
from abc import ABC, abstractmethod
import pandas as pd
from ..audio_control_cycle import  MicState
from pathlib import Path

class IAudioControlApi(ABC):
    @abstractmethod
    def status(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def graph(self) -> str:
        pass


    @abstractmethod
    def index(self) -> str:
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        pass

    @abstractmethod
    def play_audio(self, audio: bytes):
        pass

    @abstractmethod
    def set_state(self, state: MicState):
        pass

    @abstractmethod
    def get_state(self) -> MicState:
        pass

    @abstractmethod
    def get_uploaded_filename(self) -> str|None:
        pass

    @abstractmethod
    def wait_for_uploaded_filename(self, max_sleep_time_in_seconds = None) -> str:
        pass

    @abstractmethod
    def set_mic_sample(self, sample: Path):
        pass

    @abstractmethod
    def is_mic_sample_finished(self):
        pass

    @abstractmethod
    def set_volume(self, volume: float):
        pass


    def playback_mic_sample(self, sample: Path):
        self.set_mic_sample(sample)
        while not self.is_mic_sample_finished():
            time.sleep(0.1)


