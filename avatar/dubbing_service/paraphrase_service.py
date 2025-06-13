import copy
from typing import *
from ..media_library_manager import ContentManager
from eaglesong.templates import Utterance, UtterancesSequence, TemplateDub, Template, TemplateSequenceDub
from .text_processor import TextLike
from dataclasses import dataclass

@dataclass
class ParaphraseRecord:
    filename: str
    template: Template
    original_template_name: str
    used_variables_tag: str
    character: str|None = None
    user: str|None = None

    @staticmethod
    def create_variables_tag(variables: Iterable[str]):
        return ','.join(sorted(set(variables)))



@dataclass
class ParaphraseServiceSettings:
    manager: ContentManager[ParaphraseRecord]


class ParaphraseService:
    def __init__(self, settings: ParaphraseServiceSettings):
        self.settings = settings
        self.last_file_id: str|None = None


    def _paraphrase_utterance(self, u: Utterance, state) -> list[Utterance]:
        if not isinstance(u, Utterance):
            return [u]
        if u.template.get_context() is None:
            return [u]
        dub = u.template.dub
        if not isinstance(dub, TemplateDub):
            return [u]
        variables = dub.find_required_variables(u.value)
        variables_tag = ParaphraseRecord.create_variables_tag(variables)

        template_tag = {
            'original_template_name': u.template.get_name(),
            'used_variables_tag': variables_tag
        }

        template_record = self.settings.manager.find_content(state, template_tag)
        if template_record is None:
            return [u]
        self.settings.manager.feedback(template_record.filename, 'seen')
        self.last_content_id = template_record.filename
        return [template_record.template(u.value).to_str()]

    def _paraphrase_sequence(self, text: UtterancesSequence, state):
        result = []
        for u in text.utterances:
            result.extend(self._paraphrase_utterance(u, state))
        return UtterancesSequence(*result)

    def paraphrase(self, text: TextLike, state):
        if isinstance(text, str):
            return text
        elif isinstance(text, Utterance):
            return UtterancesSequence(*self._paraphrase_utterance(text, state))
        elif isinstance(text, UtterancesSequence):
            return self._paraphrase_sequence(text, state)
        else:
            raise ValueError("TextLike must be str, Utterance or UtteranceSequence")


