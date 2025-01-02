from typing import *
from eaglesong.core import Translator, TranslatorInputPackage
from kaia.dub import Template, IntentsPack
from kaia.avatar.state import RhasspyHandler


class RhasspyTextToUtteranceTranslator(Translator):
    def __init__(self,
                 inner_function,
                 intents: Iterable[IntentsPack]
                 ):
        intents = list(intents)
        if len(intents) != 1:
            raise ValueError("Exactly one intent pack is expected")
        self.handler = RhasspyHandler(intents[0].templates)
        super().__init__(
            inner_function,
            input_function_translator=self.translate_input
        )

    def translate_input(self, package: TranslatorInputPackage):
        if isinstance(package.outer_input, str):
            return self.handler.parse_string(package.outer_input)
        else:
            return package.outer_input



