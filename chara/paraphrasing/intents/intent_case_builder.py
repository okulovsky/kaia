from typing import Iterable
from grammatron import Template
from ..common import ParsedTemplate
from .modality import Modality, MODALITIES
from .intent_case import IntentCase


class IntentCaseBuilder:
    def __init__(
        self,
        templates: Iterable[Template],
        modalities: Iterable[Modality] = MODALITIES,
        languages: tuple[str, ...] = ('ru',),
    ):
        self.templates = templates
        self.modalities = tuple(modalities)
        self.languages = languages

    def _filter_templates(self, templates: Iterable[Template]) -> list[Template]:
        names = set()
        result = []
        for template in templates:
            name = template.get_name()
            if name in names:
                continue
            names.add(name)
            result.append(template)
        return result

    def create_cases(self) -> list[IntentCase]:
        parsed_templates = []
        for template in self._filter_templates(self.templates):
            parsed_templates.extend(ParsedTemplate.parse(template))

        cases = []
        for language in self.languages:
            for modality in self.modalities:
                for parsed in parsed_templates:
                    cases.append(IntentCase(parsed, language, modality))
        return cases
