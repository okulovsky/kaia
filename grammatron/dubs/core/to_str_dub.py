from typing import Any
from .dub import IDub, DubParameters
from . import parser_intructions as PI

class ToStrDub(IDub):
    def _to_str_internal(self, value, parameters: DubParameters):
        return str(value)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        raise ValueError("ToStrDub cannot be used for parsing")

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        raise ValueError("ToStrDub cannot convolute values")

