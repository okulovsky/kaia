from dataclasses import dataclass
from typing import Iterable
from ..dubs import TemplateDub, ISubSequenceDub, SequenceDub, ConstantDub, GrammarAdoptableDub, VariableDub
from .template import Template
from .collections import TemplatesCollection

@dataclass
class TemplateParserBaseLeafInfo:
    constant: ConstantDub|None
    grammar_adoptable: GrammarAdoptableDub|None
    variable: VariableDub|None

class TemplateParserBase:
    LeafInfo = TemplateParserBaseLeafInfo

    def parse(self, templates: Template|Iterable[Template]|TemplatesCollection):
        if isinstance(templates, Template):
            templates = (templates,)
        else:
            templates = tuple(templates)
        if not self.open_collection(templates):
            return
        for template_index, template in enumerate(templates):
            self.open_template(template_index, template, len(templates))
            for language_index, (language, template_dub) in enumerate(template.dub.dispatch.items()):
                if not self.open_language(language_index, language, template_dub, len(template.dub.dispatch)):
                    continue
                for sequence_index, sequence in enumerate(template_dub.sequences):
                    if not self.open_sequence(sequence_index, sequence, len(template_dub.sequences)):
                        continue
                    self._recursion(sequence)


    def _recursion(self, subsequence: ISubSequenceDub):
        subs = subsequence.get_sequence()
        if isinstance(subsequence, ConstantDub):
            self.on_leaf(TemplateParserBaseLeafInfo(subsequence, None, None))
        elif isinstance(subsequence, GrammarAdoptableDub):
            self.on_leaf(TemplateParserBaseLeafInfo(None, subsequence, None))
        elif isinstance(subsequence, VariableDub):
            self.on_leaf(TemplateParserBaseLeafInfo(None, None, subsequence))
        elif subs is None:
            raise ValueError(f"Unexpected leaf {subsequence}")
        elif self.open_subsequence(subsequence):
            for element in subs:
                self._recursion(element)

    def open_collection(self, templates: tuple[Template,...]) -> bool:
        return True

    def open_template(self, template_index: int, template: Template, total_templates: int) -> bool:
        return True

    def open_language(self, language_index: int, language: str, template_dub: TemplateDub, total_languages: int) -> bool:
        return True

    def open_sequence(self, sequence_index: int, sequence: SequenceDub, total_sequences: int) -> bool:
        return True

    def open_subsequence(self, subsequence: ISubSequenceDub) -> bool:
        return True

    def on_leaf(self, leaf_info: TemplateParserBaseLeafInfo) -> None:
        pass










