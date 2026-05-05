from abc import ABC, abstractmethod
from grammatron import PluralAgreement, GrammarAdoptableDub, OptionsDub
from typing import Any
from ..template_paraphrasing import ParsedTemplate



class IWordLocation(ABC):
    @abstractmethod
    def get(self) -> str:
        pass

    @abstractmethod
    def set(self, value: str) -> None:
        pass


class GrammarAdoptableLocation:
    def __init__(self, grammar_adoptable: GrammarAdoptableDub):
        self.grammar_adoptable = grammar_adoptable

    def get(self) -> str:
        return self.grammar_adoptable.value

    def set(self, value: str) -> None:
        self.grammar_adoptable.value = value


class OptionLocation:
    def __init__(self, dub: OptionsDub, value: Any, index: int):
        self.dub = dub
        self.value = value
        self.index = index

    def get(self) -> str:
        return self.dub.value_to_strs[self.value][self.index]

    def set(self, value: str) -> None:
        self.dub.value_to_strs[self.value][self.index] = value


class OptionHeaderLocation:
    def __init__(self, dub: OptionsDub, value: Any):
        self.dub = dub
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.dub.value_to_strs[value] = self.dub.value_to_strs[self.value]
        del self.dub.value_to_strs[self.value]





