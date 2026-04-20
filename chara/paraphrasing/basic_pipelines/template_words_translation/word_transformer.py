from chara.common import Language
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from .word_location import GrammarAdoptableLocation, OptionLocation, OptionHeaderLocation, IWordLocation
from ..template_paraphrasing.fragment_descriptors import PluralAgreementWithConstant
from dataclasses import dataclass
from ..utility_pipelines import CaseStatus
from typing import Callable

@dataclass
class WordTranslationCase:
    source: str
    target_language_code: str
    target_language_name: str
    translation: str|None = None
    status: CaseStatus = CaseStatus.not_started



class WordTransformer:
    def __init__(self,
                 templates: list[Template],
                 also_translate_options_header: bool = False
                 ):
        self.templates = templates
        self.also_translate_options_header = also_translate_options_header
        self.word_to_language_to_locations = {}
        for template in templates:
            self._parse_template(template)

    def _get_locations(self, parsed_template: ParsedTemplate) -> list[IWordLocation]:
        result = []
        for fragment in parsed_template.fragments:
            if isinstance(fragment.descriptor, PluralAgreementWithConstant):
                result.append(GrammarAdoptableLocation(fragment.descriptor.constant))
        for variable in parsed_template.variables:
            if isinstance(variable.dub, OptionsDub):
                for value in variable.dub.value_to_strs:
                    for i in range(len(variable.dub.value_to_strs[value])):
                        result.append(OptionLocation(variable.dub, value, i))
                    if self.also_translate_options_header and isinstance(value, str):
                        result.append(OptionHeaderLocation(variable.dub, value))
        return result

    def _parse_template(self, template: Template):
        parsed_template = ParsedTemplate.parse_single(template)
        language = parsed_template.original_language
        locations = self._get_locations(parsed_template)
        for location in locations:
            word = location.get()
            if word not in self.word_to_language_to_locations:
                self.word_to_language_to_locations[word] = {}
            if language not in self.word_to_language_to_locations[word]:
                self.word_to_language_to_locations[word][language] = []
            self.word_to_language_to_locations[word][language].append(location)


    def get_cases(self) -> list[WordTranslationCase]:
        cases = []
        for word in self.word_to_language_to_locations:
            for language in self.word_to_language_to_locations[word]:
                cases.append(WordTranslationCase(word, language, Language.from_code(language).name))
        return cases

    def _apply_cases(self, cases: list[WordTranslationCase], condition: Callable[[IWordLocation], bool]):
        for translation in cases:
            for location in self.word_to_language_to_locations[translation.source][translation.target_language_code]:
                if condition(location):
                    location.set(translation.translation)

    def apply_cases(self, cases: list[WordTranslationCase]):
        self._apply_cases(cases, lambda loc: not isinstance(loc, OptionHeaderLocation))
        self._apply_cases(cases, lambda loc: isinstance(loc, OptionHeaderLocation))





