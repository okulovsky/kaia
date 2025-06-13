from typing import *
from . import parser_intructions as PI
from .dub import  IDub, DubParameters, IGrammarAdoptionDub
from .constant_dub import ConstantDub
from .variable_dub import VariableDub
from dataclasses import dataclass

@dataclass
class TemplateSequenceHumanReadableFragment:
    representation: str
    template_sequence_part: ConstantDub|VariableDub|IGrammarAdoptionDub


@dataclass
class TemplateSequenceDub(IDub):
    sequence: tuple[IDub,...]
    normalized_variable_names: tuple[str,...] = ()

    @staticmethod
    def normalize(variable_names: Iterable[str]):
        return tuple(sorted(set(variable_names)))

    def __post_init__(self):
        for s in self.sequence:
            if not isinstance(s, ConstantDub) and not isinstance(s, VariableDub) and not isinstance(s, IGrammarAdoptionDub):
                raise ValueError("Every element in sequence must be ConstantDub, VariableDub or IGrammarAdoptionDub")
        self.normalized_variable_names = TemplateSequenceDub.normalize(z.variable.name for z in self.sequence if isinstance(z, VariableDub))

    def is_applicable(self, variable_names, already_normalized: bool = False):
        if not already_normalized:
            variable_names = self.normalize(variable_names)
        return self.normalized_variable_names == variable_names

    def _to_str_internal(self, value, parameters: DubParameters):
        return ''.join(dub.to_str(value, parameters) for dub in self.sequence)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        variables = {}
        parser_interfaces = []
        for dub in self.sequence:
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
        for element in self.sequence:
            if isinstance(element, VariableDub):
                convoluted_value = element._convolute_values_internal(variable_name_to_associated_values[element.variable.name], parameters)
                result[element.variable.name] = convoluted_value
        return result

    def to_human_readable_string_fragments(self, parameters: DubParameters|None = None) -> tuple[TemplateSequenceHumanReadableFragment,...]:
        result = []
        for element in self.sequence:
            if isinstance(element, ConstantDub):
                result.append(TemplateSequenceHumanReadableFragment(element.value, element))
            elif isinstance(element, VariableDub):
                result.append(TemplateSequenceHumanReadableFragment('{'+element.variable.name+'}', element))
            elif isinstance(element, IGrammarAdoptionDub):
                result.append(TemplateSequenceHumanReadableFragment('['+'|'.join(element.get_options(parameters))+']', element))
            else:
                raise ValueError("Every element in sequence must be ConstantDub, VariableDub or IGrammarAdoptionDub")
        return tuple(result)

    def to_human_readable_string(self, parameters: DubParameters|None = None):
        return ''.join(fragment.representation for fragment in self.to_human_readable_string_fragments(parameters))

