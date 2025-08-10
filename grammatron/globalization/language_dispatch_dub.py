from typing import *
from ..dubs import DubParameters, IDub, PI, ISubSequenceDub

TDub = TypeVar("TDub", bound=IDub)

class LanguageDispatchDub(IDub, Generic[TDub]):
    def __init__(self, **dispatch: TDub):
        for v in dispatch.values():
            if not isinstance(v, IDub):
                raise ValueError("Dubs are expected")
        self.dispatch: dict[str, TDub] = dispatch

    def get_dispatch(self, parameters: DubParameters) -> TDub:
        if parameters.language not in self.dispatch:
            return self.dispatch[DubParameters.default_language()]
        else:
            return self.dispatch[parameters.language]

    def _to_str_internal(self, value, parameters: DubParameters):
        return self.get_dispatch(parameters).to_str(value, parameters)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters ) -> PI.ParserData:
        return self.get_dispatch(parameters)._get_parser_data_internal(variables_stack, parameters)

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        return self.get_dispatch(parameters)._convolute_values_internal(values, parameters)


class LanguageDispatchSubSequenceDub(LanguageDispatchDub[ISubSequenceDub], ISubSequenceDub):
    def __init__(self, **dispatch: IDub):
        super().__init__(**dispatch)

    def get_sequence(self) -> tuple['ISubSequenceDub',...]|None:
        return self.get_dispatch(DubParameters()).get_sequence()

    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        return self.get_dispatch(DubParameters()).get_human_readable_representation(parameters)









