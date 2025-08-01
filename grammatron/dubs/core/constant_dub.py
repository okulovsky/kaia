from typing import Any
from .dub import IDub, DubParameters
from . import parser_intructions as PI
from .variable_dub import VariableDub
from dataclasses import dataclass
from .subsequence_dub import ISubSequenceDub

@dataclass
class ConstantDub(ISubSequenceDub):
    value: str

    def _to_str_internal(self, value, parameters: DubParameters):
        return self.value

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        return PI.ParserData(PI.ConstantParserInstruction(self.value))

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        pass

    def _convolute_to_dictionary(self, values: dict[tuple[str,...], Any], parameters: DubParameters, target: dict[str, Any]):
        pass

    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        return self.value

    def get_sequence(self) -> tuple['ISubSequenceDub',...]|None:
        return None