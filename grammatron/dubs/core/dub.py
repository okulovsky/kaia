from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import *
from . import parser_intructions as PI

if TYPE_CHECKING:
    from ...grammars.grammar_setter import GrammarSetter

class GrammarRule:
    def to_correct_form(self, text: str, value: Any, dub: 'IDub'):
        return text

    def all_morphological_forms(self, text: str, value: Any, dub: 'IDub') -> tuple[str,...]:
        return (text,)

    def get_language_name(self):
        return IDub.DEFAULT_LANGUAGE

    def merge_with_lower_priority(self, rule: GrammarRule):
        return self

    FIELD_NAME = '_predefined_grammar_rules'

@dataclass(frozen=True)
class DubParameters:
    spoken: bool = True
    language: str = 'en'
    grammar_rule: GrammarRule = field(default_factory=GrammarRule)

    def change_grammar(self, new_rule: GrammarRule|None):
        if new_rule is None:
            new_rule = GrammarRule()
        return DubParameters(self.spoken, self.language, new_rule)

    @staticmethod
    def default_language():
        return 'en'


class DubGlobalCache:
    cache: dict[int, dict[DubParameters,dict[str,Any]]] = {}


class IDub(ABC):
    def adjust_parameters(self, parameters: DubParameters|None = None) -> DubParameters:
        from ...grammars.grammar_setter import GrammarSetter
        if parameters is None:
            parameters = DubParameters()
        stored_rule: GrammarRule | None = getattr(self, GrammarRule.FIELD_NAME, {}).get(parameters.language,None)
        defaut_rule = GrammarSetter.get_default_grammar_for_language(parameters.language)

        if type(parameters.grammar_rule) is GrammarRule:
            if stored_rule is not None:
                return parameters.change_grammar(stored_rule)
            if defaut_rule is not None:
                return parameters.change_grammar(defaut_rule)
            return parameters
        else:
            if stored_rule is not None:
                return parameters.change_grammar(parameters.grammar_rule.merge_with_lower_priority(stored_rule))
            return parameters

    def to_str(self, value, parameters: DubParameters|None = None):
        return self._to_str_internal(value, self.adjust_parameters(parameters))

    @abstractmethod
    def _to_str_internal(self, value, parameters: DubParameters):
        pass


    def get_parser_data(self, parameters: DubParameters|None = None) -> PI.ParserData:
        return self._get_parser_data_internal((), self.adjust_parameters(parameters))

    @abstractmethod
    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        pass

    def convolute_values(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        return self._convolute_values_internal(values, self.adjust_parameters(parameters))

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
        c = self.get_cache(self.adjust_parameters(parameters))
        if field_name not in c:
            c[field_name] = factory(self, parameters)
        return c[field_name]

    def __del__(self):
        uid = id(self)
        if DubGlobalCache is not None and DubGlobalCache.cache is not None and uid in DubGlobalCache.cache:
            del DubGlobalCache.cache[uid]

    def as_variable(self, name: str):
        from .variable_dub import VariableDub
        return VariableDub(name, self)

    @property
    def grammar(self) -> GrammarSetter:
        from ...grammars.grammar_setter import GrammarSetter
        return GrammarSetter(self)

