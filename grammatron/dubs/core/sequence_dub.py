from typing import *
from . import parser_intructions as PI
from .dub import DubParameters
from .subsequence_dub import ISubSequenceDub
from .variable_dub import VariableDub
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class TemplateSequenceHumanReadableFragment:
    representation: str
    template_sequence_part: Union[ISubSequenceDub]


class ISequenceDub(ISubSequenceDub, ABC):
    def get_variables(self) -> tuple[VariableDub,...]:
        return tuple(c for c in self.get_leaves() if isinstance(c, VariableDub))

    def get_normalized_variables_names(self) -> tuple[str,...]:
        return ISequenceDub.normalize(v.name for v in self.get_variables())

    @staticmethod
    def normalize(variable_names: Iterable[str]):
        return tuple(sorted(set(variable_names)))

    def is_applicable(self, variable_names, already_normalized: bool = False):
        if not already_normalized:
            variable_names = self.normalize(variable_names)
        return self.get_normalized_variables_names() == variable_names

    def _to_str_internal(self, value, parameters: DubParameters):
        return ''.join(dub.to_str(value, parameters) for dub in self.get_sequence())

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        variables = {}
        parser_interfaces = []
        for dub in self.get_sequence():
            pd = dub._get_parser_data_internal(variables_stack, parameters)
            if pd.variables is not None:
                for key, value in pd.variables.items():
                    variables[key] = value
            parser_interfaces.append(pd.root)
        return PI.ParserData(
            PI.SequenceParserInstruction(tuple(parser_interfaces)),
            variables
        )

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        variable_name_to_associated_values: dict[str, dict[tuple[str,...], Any]] = {}
        for key, value in values.items():
            if len(key) == 0:
                raise ValueError(f"Value {value} was placed without path. This exceptions shouldn't occur as this error should be checked on the Template's level")
            name = key[0]
            if name not in variable_name_to_associated_values:
                variable_name_to_associated_values[name] = {}
            variable_name_to_associated_values[name][key[1:]] = value
        result = {}
        for element in self.get_sequence():
            element._convolute_to_dictionary(values, parameters, result)
        return result

    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        return ''.join(l.get_human_readable_representation() for l in self.get_leaves())



@dataclass
class SequenceDub(ISequenceDub):
    sequence: tuple[ISubSequenceDub,...]

    def __post_init__(self):
        if not isinstance(self.sequence, tuple):
            self.sequence = tuple(self.sequence)
        for index, element in enumerate(self.sequence):
            if not isinstance(element, ISubSequenceDub):
                raise ValueError(f"ISubSequenceDub was expected in the SequenceDub, but at position {index}, was {element}")


    def get_sequence(self) -> tuple[ISubSequenceDub, ...]:
        return self.sequence


    def __str__(self):
        return 'Sequence: '+self.get_human_readable_representation()
