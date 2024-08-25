from typing import *
from kaia.eaglesong.core import Translator, TranslatorInputPackage
from kaia.dub import Template
from kaia.dub.rhasspy_utils import RhasspyHandler


class RhasspyTextToUtteranceTranslator(Translator):
    def __init__(self,
                 inner_function,
                 intents: Iterable[Template]
                 ):
        self.handler = RhasspyHandler(intents)
        super().__init__(
            inner_function,
            input_function_translator=self.translate_input
        )

    def translate_input(self, package: TranslatorInputPackage):
        if isinstance(package.outer_input, str):
            return self.handler.parse_string(package.outer_input)
        else:
            return package.outer_input



