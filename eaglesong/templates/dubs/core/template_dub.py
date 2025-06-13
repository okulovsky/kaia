import traceback
from typing import *
from foundation_kaia.prompters import Prompter, ConstantTemplatePart, AddressTemplatePart
from . import parser_intructions as PI
from .dub import  IDub, DubParameters
from .constant_dub import ConstantDub
from .variable_dub import VariableDub
from .template_variable import TemplateVariable
from dataclasses import dataclass
from .template_sequence_dub import TemplateSequenceDub
from abc import ABC, abstractmethod


def convert_value_to_variables(self, value) -> Mapping[str, Any]:
    if self.data_type is not None:
        if not isinstance(value, self.data_type):
            raise ValueError(f"value is expected to be {self.data_type}, but was {value}")
        if self.value_to_variables is not None:
            return self.value_to_variables(value)
        else:
            return value.__dict__
    else:
        if self.value_to_variables is not None:
            return self.value_to_variables(value)
        if not isinstance(value, dict):
            raise ValueError(f"value is expected to be dict, but was {value}")
        return value


@dataclass
class TemplateDub(IDub, ABC):
    def __init__(self, *sequences: str|TemplateSequenceDub):
        converted = []
        for i, s in enumerate(sequences):
            if isinstance(s, str):
                converted.append(TemplateDub.parse_definition(s))
            elif isinstance(s, TemplateSequenceDub):
                converted.append(s)
            else:
                raise ValueError(f"Element must be TemplateSequenceDub or str, but at index {i} was {s}")
        if len(converted) == 0:
            raise ValueError("Sequences cannot be empty")
        self.sequences: tuple[TemplateSequenceDub, ...] = tuple(converted)


    @abstractmethod
    def value_to_variables(self, value: Any) ->dict[str,Any]:
        pass

    @abstractmethod
    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        pass

    def find_required_variables(self, value) -> tuple[str,...]:
        converted_value = self.value_to_variables(value)
        used_variables = TemplateSequenceDub.normalize(converted_value)
        return used_variables




    def _to_str_internal(self, value, parameters: DubParameters):
        converted_value = self.value_to_variables(value)
        used_variables = TemplateSequenceDub.normalize(converted_value)

        tried_templates = []
        for sequence in self.sequences:
            if sequence.is_applicable(used_variables, True):
                try:
                    return sequence.to_str(converted_value, parameters)
                except:
                    tried_templates.append(dict(sequence=str(sequence), error = traceback.format_exc()))
        if len(tried_templates) == 0:
            raise ValueError(f"Values mismatch: cannot find the sequence for variables {used_variables}. Available are: "+', '.join(str(s.normalized_variable_names) for s in self.sequences))

        strs = ['Following sequences were tried:']
        for t in tried_templates:
            strs.append(t['sequence'])
            strs.append(t['error'])
        raise ValueError("\n\n".join(strs))

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters, ) -> PI.ParserData:
        variables = {}
        union = []
        for sequence in self.sequences:
            pd = sequence._get_parser_data_internal(variables_stack, parameters)
            if pd.variables is not None:
                for key, value in pd.variables.items():
                    variables[key] = value
            union.append(pd.root)
        return PI.ParserData(
            PI.UnionParserInstruction(tuple(union)),
            variables
        )

    @staticmethod
    def parse_definition(line: str) -> TemplateSequenceDub:
        prompt = Prompter(line)
        result = []
        for part in prompt.template:
            if isinstance(part, ConstantTemplatePart):
                result.append(ConstantDub(part.value))
            elif isinstance(part, AddressTemplatePart):
                info = part.misc
                if not isinstance(info, TemplateVariable):
                    raise ValueError("Only TemplateVariables can be used in these templates")
                if info.name is not None:
                    result.append(VariableDub(info))
                else:
                    result.append(info.dub)
        return TemplateSequenceDub(tuple(result))


    def _preconvolute(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        keys = set()
        for key in values:
            if len(key) == 0:
                raise ValueError("Cannot convolute: Template should not have empty keys")
            keys.add(key[0])
        provided_variables = TemplateSequenceDub.normalize(keys)
        tried_templates = []
        for sequence in self.sequences:
            if sequence.is_applicable(provided_variables, True):
                try:
                    return sequence._convolute_values_internal(values, parameters)
                except:
                    tried_templates.append(dict(sequence=str(sequence), error=traceback.format_exc()))
        if len(tried_templates) == 0:
            raise ValueError(f"Values mismatch: cannot find the sequence for {provided_variables}")

        strs = ['Following sequences were tried:']
        for t in tried_templates:
            strs.append(t['sequence'])
            strs.append(t['error'])
        raise ValueError("\n\n".join(strs))

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        variables = self._preconvolute(values, parameters)
        return self.variables_to_value(variables)



class DataclassTemplateDub(TemplateDub):
    def __init__(self, _type: Type, *definitions: str):
        self._type = _type
        super().__init__(*definitions)

    def value_to_variables(self, value: Any):
        if not isinstance(value, self._type):
            raise ValueError(f"Expected instance of {self._type}, but was {value}")
        return {k:v for k,v in value.__dict__.items() if v is not None}

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return self._type(**variables)


class DictTemplateDub(TemplateDub):
    def __init__(self, *definitions: str|TemplateSequenceDub):
        super().__init__(*definitions)

    def value_to_variables(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"Expected dict, but was {value}")
        return value

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return variables


class FunctionalTemplateDub(TemplateDub):
    def __init__(self,
                 definitions: Iterable[Union[str, TemplateDub]],
                 value_to_variables: Callable[[Any], dict],
                 variables_to_value: Callable[[dict], Any]
                 ):
        self._value_to_variables = value_to_variables
        self._variables_to_value = variables_to_value
        super().__init__(*definitions)

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return self._variables_to_value(variables)

    def value_to_variables(self, value: Any) ->dict[str,Any]:
        return self._value_to_variables(value)

