from typing import Any

from .dub import IDub, DubParameters
from . import parser_intructions as PI
from dataclasses import dataclass, field
from .to_str_dub import ToStrDub
from .subsequence_dub import ISubSequenceDub

@dataclass
class VariableAssignment:
    variable: 'VariableDub'
    value: Any

@dataclass
class VariableDub(ISubSequenceDub):
    name: str
    dub: IDub = field(default_factory=ToStrDub)
    description: str | None = None

    def rename(self, name: str) -> 'VariableDub':
        return VariableDub(
            name,
            self.dub,
            self.description
        )

    def assign(self, value):
        return VariableAssignment(self, value)

    def _to_str_internal(self, value, parameters: DubParameters):
        if self.name not in value:
            raise ValueError(f"Variable {self.name} is not found among the variables")
        return self.dub.to_str(value[self.name], parameters)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters,) -> PI.ParserData:
        return self.dub._get_parser_data_internal(variables_stack+(self.name,), parameters)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        new_values = {key[1:]:value for key, value in values.items() if len(key)>0 and key[0]==self.name}
        return self.dub.convolute_values(new_values, parameters)

    def _convolute_to_dictionary(self, values: dict[tuple[str,...], Any], parameters: DubParameters, target: dict[str, Any]):
        target[self.name] = self.convolute_values(values, parameters)

    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        return '{'+self.name+'}'

    def get_sequence(self) -> tuple['ISubSequenceDub',...]|None:
        return None