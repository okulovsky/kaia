from typing import *
from kaia.kaia.audio_control import AudioControlCommand, MicState
from kaia.eaglesong.core import Translator, Listen

from .audio_control_listen import AudioControlListen




class AudioControlTranslator(Translator):
    def __init__(self, inner_function, handler):
        from .audio_control_handler import AudioControlHandler
        self.handler: AudioControlHandler = handler
        self._last_listen: None|AudioControlListen = None
        super().__init__(
            inner_function,
            input_function_translator=self._translate_input,
            output_function_translator=self._translate_output
        )

    def _translate_input(self, input: Translator.InputPackage):
        if isinstance(input.outer_input, AudioControlCommand):
            last_listen = self._last_listen
            self._last_listen = None
            if last_listen is None:
                return self.handler.run_rhasspy_recognition(input.outer_input.filename)
            elif last_listen.nlu == AudioControlListen.NLU.Rhasspy:
                return self.handler.run_rhasspy_recognition(input.outer_input.filename)
            else:
                return self.handler.run_whisper_recognition(input.outer_input.filename, last_listen.whisper_prompt)
        else:
            return input.outer_input


    def _translate_output(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, AudioControlListen):
            self._last_listen = output.inner_output
            if output.inner_output.open_mic:
                self.handler.audio_control_api.set_state(MicState.Open)
        return output.inner_output


