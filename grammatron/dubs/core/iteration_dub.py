from typing import Any
from .dub import IDub, DubParameters
from ..core import parser_intructions as PI

class IterationDub(IDub):
    def __init__(self, inner: IDub, _type: type = tuple):
        self.inner = inner

    def _to_str_internal(self, value, parameters: DubParameters):
        return ''.join(self.inner.to_str(v, parameters) for v in value)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        root = PI.IterationParserInstruction(
            PI.SubdomainInstruction(
                variables_stack,
                self.inner._get_parser_data_internal((), parameters)
            )
        )
        return PI.ParserData(root)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        if () not in values:
            raise ValueError("Excepted variables at the root")
        if not isinstance(values[()], list):
            raise ValueError(f"Variables expected to be list, but was {values}")
        return tuple(
            self.inner.convolute_values(v, parameters)
            for v in values[()]
        )




