from typing import Any
from .dub import IDub, DubParameters
from . import parser_intructions as PI, VariableDub
from dataclasses import dataclass
from .subsequence_dub import ISubSequenceDub

@dataclass
class GrammarAdoptableDub(ISubSequenceDub):
    value: str

    def _to_str_internal(self, value, parameters: DubParameters):
        return parameters.grammar_rule.to_correct_form(self.value, None, self)

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        variants = parameters.grammar_rule.all_morphological_forms(self.value, None, self)
        return PI.ParserData(
            PI.UnionParserInstruction(tuple(
                PI.ConstantParserInstruction(option) for option in variants
            )))

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        pass

    def _convolute_to_dictionary(self, values: dict[tuple[str,...], Any], parameters: DubParameters, target: dict[str, Any]):
        pass

    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        variants = parameters.grammar_rule.all_morphological_forms(self.value, None, self)
        if len(variants) > 2:
            variants = variants[:2]+('...',)
        return '['+'|'.join(variants)+']'

    def get_sequence(self) -> tuple['ISubSequenceDub',...]|None:
        return None