from typing import Any

from ..core import IGrammarAdoptionDub, parser_intructions as PI, DubParameters
from dataclasses import dataclass

@dataclass
class PluralAgreement(IGrammarAdoptionDub):
    field_to_agree_on: str
    singular_form: str | None = None
    plural_form: str | None = None

    def __post_init__(self):
        if self.singular_form is None:
            if self.field_to_agree_on.endswith('s'):
                self.singular_form = self.field_to_agree_on[:-1]
                self.plural_form = self.field_to_agree_on
            else:
                self.singular_form = self.field_to_agree_on
                self.plural_form = self.singular_form+'s'
        elif self.plural_form is None:
            self.plural_form = self.singular_form+'s'

    def _to_str_internal(self, value, parameters: DubParameters|None = None):
        if value[self.field_to_agree_on] == 1:
            return self.singular_form
        return self.plural_form

    def _get_parser_data_internal(self, variables_stack: tuple[str,...], parameters: DubParameters) -> PI.ParserData:
        return PI.ParserData(
            PI.UnionParserInstruction((
                PI.ConstantParserInstruction(self.singular_form),
                PI.ConstantParserInstruction(self.plural_form)
            ))
        )

    def _convolute_values_internal(self, values: dict[tuple[str,...], Any], parameters: DubParameters):
        raise ValueError("PluralAgreementDub cannot convolute values")

    def _get_options_internal(self, parameters: DubParameters):
        return self.singular_form, self.plural_form