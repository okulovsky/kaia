from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import *
from . import parser_intructions as PI


@dataclass(frozen=True)
class DubParameters:
    spoken: bool = True
    language: Optional[str] = None

    def __post_init__(self):
        if self.language is None:
            object.__setattr__(self, 'language', IDub.DEFAULT_LANGUAGE)



class DubGlobalCache:
    cache: dict[int, dict[DubParameters,dict[str,Any]]] = {}


class IDub(ABC):
    def parameters_or_default(self, parameters: DubParameters|None = None):
        if parameters is None:
            return IDub.default_parameters()
        else:
            return parameters

    def to_str(self, value, parameters: DubParameters|None = None):
        return self._to_str_internal(value, self.parameters_or_default(parameters))

    @abstractmethod
    def _to_str_internal(self, value, parameters: DubParameters):
        pass


    def get_parser_data(self, parameters: DubParameters|None = None) -> PI.ParserData:
        return self._get_parser_data_internal((), self.parameters_or_default(parameters))

    @abstractmethod
    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        pass

    def convolute_values(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        return self._convolute_values_internal(values, self.parameters_or_default(parameters))

    @abstractmethod
    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        pass


    def get_cache(self, parameters: DubParameters) -> Any:
        uid = id(self)
        if uid not in DubGlobalCache.cache:
            DubGlobalCache.cache[uid] = {}
        if parameters not in DubGlobalCache.cache[uid]:
            DubGlobalCache.cache[uid][parameters] = {}
        return DubGlobalCache.cache[uid][parameters]

    def get_cached_value(self,
                         factory: Callable[['IDub',DubParameters], Any],
                         parameters: DubParameters|None = None,
                         field_name: str|None = None
                         ):
        if field_name is None:
            field_name = factory.__name__
        c = self.get_cache(self.parameters_or_default(parameters))
        if field_name not in c:
            c[field_name] = factory(self, parameters)
        return c[field_name]

    def __del__(self):
        uid = id(self)
        if uid in DubGlobalCache.cache:
            del DubGlobalCache.cache[uid]

    DEFAULT_LANGUAGE = 'en'

    @staticmethod
    def default_parameters() -> DubParameters:
        return DubParameters(True, IDub.DEFAULT_LANGUAGE)

    def as_variable(self, name: str|None = None):
        from .template_variable import TemplateVariable
        return TemplateVariable(name, self)

class IGrammarAdoptionDub(IDub, ABC):
    def get_options(self, parameters: DubParameters|None = None) -> tuple[str,...]:
        return self._get_options_internal(self.parameters_or_default(parameters))

    @abstractmethod
    def _get_options_internal(self, parameters: DubParameters) -> tuple[str,...]:
        pass


