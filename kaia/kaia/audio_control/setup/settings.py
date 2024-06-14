from typing import *
from dataclasses import dataclass, field
from .. import core as ac
from pathlib import Path
from kaia.avatar.dub.core import RhasspyAPI
from kaia.brainbox.deciders.api import WhisperAPI
from .pyaudio_output import PyaudioOutput
from .pyaudio_input import PyAudioInput
from .pipelines import PorcupinePipeline, BuffererPipeline, BuffererPipelineSettings
from .pvrecorder_input import PvRecorderInput
from .play_output import PlayOutput
from enum import Enum



@dataclass
class AudioControlSettings:
    class Environments(Enum):
        Test = 0
        PyAudio = 1
        PvRecorderAndPlay = 2

    mic_data: ac.MicData | None = None
    mic_device_index: int = -1
    silence_level: float = 1000
    silence_margin_in_seconds: float = 1
    max_length_in_seconds: float = 10
    max_leading_length_in_seconds: Optional[float] = 10
    load_mic_samples: Optional[Iterable[Path]] = None
    pause_between_iterations_in_seconds: float = 0
    rhasspy_api: RhasspyAPI | None = None
    whisper_api: WhisperAPI | None = None
    awake_template: ac.AudioSampleTemplate| None = None
    confirmed_template: ac.AudioSampleTemplate| None = None
    open_template: ac.AudioSampleTemplate|None = None
    error_template: ac.AudioSampleTemplate|None = None
    port: int = 12111
    add_debug_output: bool = False
    environment: Environments = Environments.Test
    play_api_address: str | None = '127.0.0.1:12001'

    def __post_init__(self):
        if self.environment == AudioControlSettings.Environments.Test:
            self.awake_template = ac.AudioSampleTemplate(b'awake')
            self.confirmed_template = ac.AudioSampleTemplate(b'confirmed')
            self.open_template = ac.AudioSampleTemplate(b'open')
            self.error_template = ac.AudioSampleTemplate(b'error')
            self.max_leading_length_in_seconds = None
        else:
            sounds = Path(__file__).parent
            if self.open_template is None:
                self.open_template = ac.AudioSampleTemplate.from_file(sounds / 'beep_hi.wav')
            if self.confirmed_template is None:
                self.confirmed_template = ac.AudioSampleTemplate.from_file(sounds / 'beep_lo.wav')
            if self.awake_template is None:
                self.awake_template = ac.AudioSampleTemplate.from_file(sounds / 'beep_hi.wav')
            if self.error_template is None:
                self.error_template = ac.AudioSampleTemplate.from_file(sounds / 'beep_error.wav')



    def create_bufferer_pipeline_settings(self):
        return BuffererPipelineSettings(
            self.mic_data,
            self.silence_level,
            self.silence_margin_in_seconds,
            self.max_length_in_seconds,
            self.max_leading_length_in_seconds
        )

    def create_input_and_output(self):
        if self.environment == AudioControlSettings.Environments.Test:
            input = ac.FakeInput(mic_inputs=self.load_mic_samples)
            output = ac.FakeOutput()
        elif self.environment == AudioControlSettings.Environments.PyAudio:
            if self.mic_data is None:
                raise ValueError("Mic_data must be set if used with pyaudio")
            input = PyAudioInput(self.mic_device_index, chunk = self.mic_data.frame_length)
            output = PyaudioOutput()
        elif self.environment == AudioControlSettings.Environments.PvRecorderAndPlay:
            input = PvRecorderInput(self.mic_device_index)
            self.mic_data = input.get_mic_data()
            output = PlayOutput(self.play_api_address)
        else:
            raise ValueError(f"Unexpected environment {self.environment}")
        return input, output

    def create_audio_control(self):
        input, output = self.create_input_and_output()

        wake_pipeline = PorcupinePipeline('porcupine', 'awake', 'rhasspy')
        pipeline_settings = self.create_bufferer_pipeline_settings()
        rhasspy_pipeline = BuffererPipeline(
            'rhasspy',
            pipeline_settings,
            'confirmed',
            self.rhasspy_api.recognize_bytes,
            None,
            'error'
        )
        whisper_pipeline = BuffererPipeline(
            'whisper',
            pipeline_settings,
            'confirmed',
            self.whisper_api.transcribe_text_only,
            'open',
            'error'
        )

        debug_console = None
        if self.add_debug_output:
            debug_console = ac.ConsoleControlDebugConsole()

        cc = ac.AudioControl(
            input,
            output,
            wake_pipeline,
            [
                rhasspy_pipeline,
                whisper_pipeline
            ],
            {
                'awake': self.awake_template,
                'confirmed': self.confirmed_template,
                'open': self.open_template,
                'error': self.error_template
            },
            self.pause_between_iterations_in_seconds,
            debug_console
        )
        return cc
