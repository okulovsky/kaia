from typing import Any
import random
from .dub import IDub, DubParameters
from . import parser_intructions as PI

class ToStrDub(IDub):
    def __init__(self, *examples: str):
        if len(examples) == 0:
            self.examples = None
        else:
            self.examples = tuple(examples)

    def generate_random_values(self, n: int) -> list[str]:
        if self.examples is None:
            raise NotImplementedError("ToStrDub requires explicit examples to generate random values")
        return [random.choice(self.examples) for _ in range(n)]

    def _to_str_internal(self, value, parameters: DubParameters):
        result = parameters.grammar_rule.to_correct_form(str(value), value, self)
        return result

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        raise ValueError("ToStrDub cannot be used for parsing")

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        raise ValueError("ToStrDub cannot convolute values")

