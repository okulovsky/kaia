from chara.common import Chara, ICase, CaseCollection, Language, BrainBoxCasePipeline
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from .word_location import GrammarAdoptableLocation, OptionLocation, OptionHeaderLocation, IWordLocation
from ..template_paraphrasing.fragment_descriptors import PluralAgreementWithConstant
from dataclasses import dataclass
from typing import Callable, Iterable
from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder


@dataclass
class WordTranslationCase(ICase):
    source: str
    target_language_code: str
    target_language_name: str
    translation: str|None = None


class WordTranslation:
    Case = WordTranslationCase

    def __init__(self,
                 templates: list[Template],
                 also_translate_options_header: bool = False
                 ):
        self.templates = templates
        self.also_translate_options_header = also_translate_options_header
        self.word_to_language_to_locations = {}

    def prepare(self) -> CaseCollection[WordTranslationCase]:
        for template in self.templates:
            if not hasattr(template, '_case'):
                source_language='x'
            else:
                from ..template_paraphrasing import ParaphraseCase
                stored_case: ParaphraseCase = template._case
                source_language = stored_case.parsed_template.original_language
            parsed_template = ParsedTemplate.parse_single(template)
            language = parsed_template.original_language
            if language == source_language:
                continue
            locations = self._get_locations(parsed_template)
            for location in locations:
                word = location.get()
                if word not in self.word_to_language_to_locations:
                    self.word_to_language_to_locations[word] = {}
                if language not in self.word_to_language_to_locations[word]:
                    self.word_to_language_to_locations[word][language] = []
                self.word_to_language_to_locations[word][language].append(location)

        cases = []
        for word in self.word_to_language_to_locations:
            for language in self.word_to_language_to_locations[word]:
                cases.append(WordTranslationCase(word, language, Language.from_code(language).name))
        return CaseCollection(cases)

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


    def _apply_cases(self, cases: list[WordTranslationCase], condition: Callable[[IWordLocation], bool]):
        for translation in cases:
            for location in self.word_to_language_to_locations[translation.source][translation.target_language_code]:
                if condition(location):
                    location.set(translation.translation)

    def apply(self, cases: Iterable[WordTranslationCase]) -> list[Template]:
        cases = list(cases)
        self._apply_cases(cases, lambda loc: not isinstance(loc, OptionHeaderLocation))
        self._apply_cases(cases, lambda loc: isinstance(loc, OptionHeaderLocation))
        return self.templates

    class Pipeline:
        def __init__(self, task_builder: PromptTaskBuilder, ):
            self.task_builder = task_builder
            self.task_builder.set_prompt(Path(__file__).parent / 'prompt.jinja')

        def _merge(self, case: WordTranslationCase, option: str):
            case.translation = option

        def __call__(self, cases: CaseCollection[WordTranslationCase]) -> CaseCollection[WordTranslationCase]:
            pipe = BrainBoxCasePipeline(self.task_builder, self._merge)
            result = Chara.call(pipe.__call__)(cases.successes_collection).raise_if_all_errors()
            return CaseCollection(cases.errors, result)
