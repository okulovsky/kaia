from abc import ABC, abstractmethod
from grammatron import VariableDub, GrammarAdoptableDub
from dataclasses import dataclass

class IFragmentDescriptor(ABC):
    @abstractmethod
    def get_description(self, example: str) -> str:
        pass

    @abstractmethod
    def get_representation(self) -> str:
        pass

@dataclass
class VariableFragmentDescriptor(IFragmentDescriptor):
    variable: VariableDub

    def get_description(self, example: str) -> str:
        result = ""
        if self.variable.description is not None:
            result += self.variable.description
            if not result.endswith('.'):
                result+='.'
            result += ' '
        result += f'Example: "{example}".'
        return result

    def get_representation(self) -> str:
        return '{'+self.variable.name+'}'

@dataclass
class PluralAgreementWithConstant(IFragmentDescriptor):
    count: VariableDub
    constant: GrammarAdoptableDub

    def get_description(self, example: str) -> str:
        result = f'A grammatically correct agreement of numeric variable `{self.count.name}` with the word "{self.constant.value}". '
        result += f'Example: "{example}". '
        if self.count.description is not None:
            result += f"Meaning of `{self.count.name}`: {self.count.description}."
        return result.strip()

    def get_representation(self) -> str:
        return '{'+self.count.name+'+'+self.constant.value+'}'


@dataclass
class PluralAgreementWithVariable(IFragmentDescriptor):
    count: VariableDub
    variable: VariableDub

    def get_description(self, example: str) -> str:
        result = f"A grammatically correct agreement of numeric variable `{self.count.name}` with the string variable `{self.variable.name}`. "
        result += f'Example: "{example}". '
        if self.count.description is not None:
            result += f"Meaning of `{self.count.name}`: {self.count.description}. "
        if self.variable.description is not None:
            result += f"Meaning of `{self.variable.name}`: {self.variable.description}. "
        return result.strip()

    def get_representation(self) -> str:
        return '{'+self.count.name+'+'+self.variable.name+'}'









