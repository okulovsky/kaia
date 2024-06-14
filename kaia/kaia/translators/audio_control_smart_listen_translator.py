from dataclasses import dataclass
from ..audio_control.core import AudioControlAPI
from kaia.eaglesong.core import Translator, TranslatorOutputPackage, Listen as _Listen, TranslatorInputPackage
from typing import *


@dataclass
class Listen(_Listen):
    def __init__(self):
        self.has_open_mic = False
        self.recognizer = None

    def open_mic(self) -> 'Listen':
        self.has_open_mic = True
        return self

    def recognize(self, recognizer: Callable[[str],Any]) -> 'Listen':
        self.recognizer = recognizer
        return self


class AudioControlListenTranslator(Translator):
    def __init__(self,
                 inner_function,
                 api: AudioControlAPI,
                 open_mic_mode: str,
                 ):
        self.api = api
        self.open_mic_mode = open_mic_mode
        self.last_recognizer: Callable[[str], Any] | None = None
        super().__init__(
            inner_function,
            output_function_translator=self.translate_output,
            input_function_translator=self.translate_input
        )

    def translate_input(self, package: TranslatorInputPackage):
        if not isinstance(package.outer_input, str):
            if self.last_recognizer is not None:
                return self.last_recognizer(package.outer_input)
        return package.outer_input


    def translate_output(self, package: TranslatorOutputPackage):
        if not isinstance(package.inner_output, Listen):
            return package.inner_output
        if package.inner_output.has_open_mic:
            self.api.set_mode(self.open_mic_mode)
            self.last_recognizer = package.inner_output.recognizer
        else:
            self.last_recognizer = None
        return package.inner_output




