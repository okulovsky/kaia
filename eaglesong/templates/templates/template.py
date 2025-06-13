from typing import *
from ..dubs import (
    DictTemplateDub, DataclassTemplateDub, RegexParser, TemplateVariable,
    TemplateVariableAssignment, VariableDub, TemplateSequenceDub, TemplateDub
)
from copy import copy, deepcopy
from foundation_kaia.prompters import Prompter
from dataclasses import dataclass
from .template_base import TemplateBase


@dataclass
class TemplateContext:
    context: Prompter|None = None
    reply_to: Tuple['Template',...] = None
    reply_details: Prompter|None = None


class Template(TemplateBase[TemplateDub]):
    Variable = TemplateVariable

    def __init__(self, *args: str):
        self._args = args
        super().__init__(DictTemplateDub(*args), None)


    def with_type(self, _type: Type) -> 'Template':
        obj = self.clone()
        obj._type = _type
        obj._dub = DataclassTemplateDub(_type, *self._args)
        return obj

    @property
    def string_templates(self) -> list[str]:
        return [s.to_human_readable_string() for s in self.dub.sequences]

    @property
    def attached_variables(self) -> dict[str, TemplateVariable]:
        result = {}
        for sequence in self.dub.sequences:
            for part in sequence.sequence:
                if isinstance(part, VariableDub):
                    result[part.variable.name] = part.variable
        return result

    def substitute(self, **new_dubs) -> 'Template':
        obj = self.clone()
        new_sequences = []
        for sequence in obj.dub.sequences:
            new_sequence = []
            for element in sequence.sequence:
                if isinstance(element, VariableDub):
                    variable = element
                    for name in new_dubs:
                        if variable.variable.name == name:
                            new_variable_info = copy(variable.variable)
                            new_variable_info.dub = new_dubs[name]
                            variable = VariableDub(new_variable_info)
                            break
                    new_sequence.append(variable)
                else:
                    new_sequence.append(element)
            new_sequences.append(TemplateSequenceDub(tuple(new_sequence)))
        obj._dub.sequences = tuple(new_sequences)
        return obj

    def _get_single_attached_subdub_name(self) -> str|None:
        if len(self.attached_variables) == 1:
            return list(self.attached_variables)[0]
        return None

