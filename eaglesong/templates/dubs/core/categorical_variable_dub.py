from typing import *
from abc import ABC, abstractmethod
from .dub import IDub, DubParameters, DubGlobalCache
from . import parser_intructions as PI


def string_values_to_values(dub: IDub, parameters: DubParameters):
    if not isinstance(dub, CategoricalVariableDub):
        raise ValueError("Only available for CategoricalVariableDub")
    values = dub.get_values()
    value_string_to_value = {}
    for v in values:
        for s in dub.value_to_all_strs(v, parameters, True):
            value_string_to_value[s] = v
    return value_string_to_value


class CategoricalVariableDub(IDub, ABC):
    @abstractmethod
    def get_values(self):
        pass

    def _to_str_internal(self, value, parameters: DubParameters):
        for result in self.value_to_all_strs(value, parameters, True):
            return result

    @abstractmethod
    def value_to_all_strs(self, value, parameters: DubParameters, first_only: bool):
        pass

    def _get_parser_data_internal(self,  variables_stack: tuple[str,...], parameters: DubParameters,) -> PI.ParserData:
        value_string_to_value = self.get_cached_value(string_values_to_values, parameters)
        return PI.ParserData(
            PI.VariableParserInstruction(variables_stack),
            {
                variables_stack: PI.VariableInfo(value_string_to_value)
            }
        )

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        if len(values) != 1:
            raise ValueError(f"CategoricalVariableDub can only convolute a single variable values, but was {values}")
        root = list(values)[0]
        if root!=():
            raise ValueError(f"CategoricalVariableDub can only convolute variable with no path, but the path was: {root}")
        return values[root]
