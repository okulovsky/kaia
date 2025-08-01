from typing import *
from grammatron import Utterance, UtterancesSequence, TemplateDub, Template, DubParameters, LanguageDispatchDub
from dataclasses import dataclass
from .common.content_manager import ContentManager
from .common import PlayableTextMessage, UtteranceSequenceCommand, TextInfo, State, AvatarService

@dataclass
class ParaphraseRecord:
    filename: str
    template: Template
    original_template_name: str
    used_variables_tag: str
    language: str
    character: str|None = None
    user: str|None = None

    @staticmethod
    def create_variables_tag(variables: Iterable[str]):
        return ','.join(sorted(set(variables)))

    def exact_match_values(self):
        return (self.original_template_name, self.used_variables_tag, self.character, self.user)



class ParaphraseService(AvatarService):
    def __init__(self, state: State, paraphrases_content_manager: ContentManager[ParaphraseRecord]):
        self.state = state
        self.paraphrases_content_manager = paraphrases_content_manager

    def _paraphrase_utterance(self, u: Utterance, info: TextInfo) -> Utterance:
        if not isinstance(u, Utterance):
            return u
        if u.template.get_context() is None:
            return u
        dub = u.template.dub
        language = info.language
        if not isinstance(dub, LanguageDispatchDub):
            return u
        if language not in dub.dispatch:
            return u
        dub = dub.dispatch[language]
        if not isinstance(dub, TemplateDub):
            return u

        variables = dub.find_required_variables(u.value)
        variables_tag = ParaphraseRecord.create_variables_tag(variables)

        template_tag = {
            'original_template_name': u.template.get_name(),
            'used_variables_tag': variables_tag,
            'language': language,
        }
        template_record = self.paraphrases_content_manager.match().strong(template_tag).weak(self.state.__dict__).find_content()
        if template_record is None:
            return u
        self.paraphrases_content_manager.feedback(template_record.filename, 'seen')
        self.last_content_id = template_record.filename
        return template_record.template(u.value)


    def __call__(self, text: PlayableTextMessage[UtteranceSequenceCommand]) -> PlayableTextMessage[UtteranceSequenceCommand]:
        sequence = text.text.utterances_sequence
        paraphrase = []
        for u in sequence.utterances:
            paraphrase.append(self._paraphrase_utterance(u, text.info))
        return PlayableTextMessage[UtteranceSequenceCommand](
            UtteranceSequenceCommand(UtterancesSequence(*paraphrase)),
            text.info
        ).as_propagation_confirmation_to(text)

    def requires_brainbox(self):
        return False

