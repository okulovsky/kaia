from typing import Any

from .dub import IDub, DubParameters
from . import parser_intructions as PI
from dataclasses import dataclass
from .template_variable import TemplateVariable

@dataclass
class VariableDub(IDub):
    variable: TemplateVariable

    def _to_str_internal(self, value, parameters: DubParameters):
        if self.variable.name not in value:
            raise ValueError(f"Variable {self.variable.name} is not found among the variables")
        return self.variable.dub.to_str(value[self.variable.name], parameters)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters,) -> PI.ParserData:
        return self.variable.dub._get_parser_data_internal(variables_stack+(self.variable.name,), parameters)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        return self.variable.dub.convolute_values(values, parameters)