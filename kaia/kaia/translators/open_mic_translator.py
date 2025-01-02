from dataclasses import dataclass
from .partial_listen_translator import PartialListenTranslator
from kaia.kaia.audio_control import AudioControlApi, MicState

@dataclass
class OpenMic:
    open_mic: bool = True

class OpenMicTranslator(PartialListenTranslator):
    def __init__(self, inner_function, audio_control_api: AudioControlApi):
        self.audio_control_api = audio_control_api
        super().__init__(
            inner_function,
            OpenMic
        )

    def captures_input(self, input):
        return False

    def observe_output(self, payload, output):
        if payload is not None and isinstance(payload, OpenMic):
            self.audio_control_api.set_state(MicState.Open)
