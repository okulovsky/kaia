from typing import Any
from .dub import IDub, DubParameters
from . import parser_intructions as PI
from dataclasses import dataclass

@dataclass
class ConstantDub(IDub):
    value: str

    def _to_str_internal(self, value, parameters: DubParameters):
        return self.value

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        return PI.ParserData(PI.ConstantParserInstruction(self.value))

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        raise ValueError("ConstantDub cannot convolute values")
