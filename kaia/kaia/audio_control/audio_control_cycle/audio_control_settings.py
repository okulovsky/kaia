from typing import *
from dataclasses import dataclass, field
from pathlib import Path
from ..inputs import IAudioInput, PyAudioInput, PvRecorderInput, FakeInput
from ..outputs import IAudioOutput, PyaudioOutput, PlayOutput, Recording, FakeOutput
from ..wakeword import IWakeWordDetector, PorcupineDetector
from ..wav_streaming import WavStreamingApi, WavApiSettings
from enum import Enum


@dataclass
class Drivers:
    input: IAudioInput
    output: IAudioOutput
    wakeword: IWakeWordDetector
    streaming_api: WavStreamingApi



@dataclass
class AudioControlSettings:
    class Environments(Enum):
        Test = 0
        PyAudio = 1
        PvRecorderAndPlay = 2

    wav_streaming_address: None|str = '127.0.0.1:13000'
    sample_rate: int = 16000
    frame_length: int = 512
    mic_device_index: int = -1
    silence_level: float = 1000
    silence_margin_in_seconds: float = 1
    max_length_in_seconds: float = 10
    max_leading_length_in_seconds: Optional[float] = 10
    load_mic_samples: Optional[Iterable[Path]] = None
    pause_between_iterations_in_seconds: float = 0
    confirmed_recording: Recording|None = None
    open_recording: Recording|None = None
    error_recording: Recording|None = None
    port: int = 12111
    environment: Environments = Environments.Test
    play_api_address: str | None = '127.0.0.1:13001'
    max_log_entries: int = 20
    max_levels_entries_in_seconds = 60

    def __post_init__(self):
        if self.environment == AudioControlSettings.Environments.Test:
            self.confirmed_recording = Recording(b'confirmed')
            self.open_recording = Recording(b'open')
            self.error_recording = Recording(b'error')
            self.max_leading_length_in_seconds = None
        else:
            sounds = Path(__file__).parent.parent/'files'
            if self.open_recording is None:
                self.open_recording = Recording.from_file(sounds / 'beep_hi.wav')
            if self.confirmed_recording is None:
                self.confirmed_recording = Recording.from_file(sounds / 'beep_lo.wav')
            if self.error_recording is None:
                self.error_recording = Recording.from_file(sounds / 'beep_error.wav')

    def create_drivers(self):
        if self.environment == AudioControlSettings.Environments.Test:
            input = FakeInput(mic_inputs=self.load_mic_samples)
            output = FakeOutput()
        elif self.environment == AudioControlSettings.Environments.PyAudio:
            input = PyAudioInput(self.mic_device_index, chunk = self.frame_length)
            output = PyaudioOutput()
        elif self.environment == AudioControlSettings.Environments.PvRecorderAndPlay:
            input = PvRecorderInput(self.mic_device_index)
            self.sample_rate = input.get_sample_rate()
            output = PlayOutput(self.play_api_address)
        else:
            raise ValueError(f"Unexpected environment {self.environment}")
        api = WavStreamingApi(WavApiSettings(self.sample_rate, self.frame_length, self.wav_streaming_address))
        return Drivers(input, output, PorcupineDetector(), api)

    @property
    def seconds_in_one_frame(self):
        return self.frame_length/self.sample_rate


    def create_audio_control(self):
        from .audio_control_cycle import AudioControlCycle
        return AudioControlCycle(self)