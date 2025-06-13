from typing import Any
from .dub import IDub, DubParameters
from . import parser_intructions as PI


class LanguageDispatchDub(IDub):
    def __init__(self, **dispatch: IDub):
        self.dispatch = dispatch

    def get_dispatch(self, parameters: DubParameters):
        if parameters.language not in self.dispatch:
            return self.dispatch[IDub.DEFAULT_LANGUAGE]
        else:
            return self.dispatch[parameters.language]

    def _to_str_internal(self, value, parameters: DubParameters):
        return self.get_dispatch(parameters).to_str(value, parameters)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters ) -> PI.ParserData:
        return self.get_dispatch(parameters)._get_parser_data_internal(variables_stack, parameters)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        return self.get_dispatch(parameters)._convolute_values_internal(values, parameters)






