from typing import Callable
from ...core import Automaton, ContextRequest, AutomatonExit, TranslatorInputPackage, Translator
from .primitives import TgUpdatePackage

def _simplify_input(input: TranslatorInputPackage):
    if isinstance(input.outer_input, TgUpdatePackage):
        return input.outer_input.update
    else:
        return input


class TelegramSimplifier(Translator):
    def __init__(self, inner):
        super().__init__(inner, input_function_translator=_simplify_input)