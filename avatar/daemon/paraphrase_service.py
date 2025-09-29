import os
from typing import *
from grammatron import Utterance, UtterancesSequence, TemplateDub, Template, DubParameters, LanguageDispatchDub
from dataclasses import dataclass
from .common.content_manager import IContentStrategy, ContentManager, DataClassDataProvider
from .common import PlayableTextMessage, UtteranceSequenceCommand, TextInfo, State, AvatarService, message_handler, InitializationEvent
from copy import copy
from yo_fluq import FileIO

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
    def __init__(self, state: State, content_strategy: IContentStrategy|None = None):
        self.state = state
        self.content_strategy = content_strategy
        self.paraphrases_content_manager: ContentManager|None = None


    @message_handler
    def on_initialize(self, message: InitializationEvent) -> None:
        records = []
        if not self.resources_folder.is_dir():
            os.makedirs(self.resources_folder)
        files = [file for file in os.listdir(self.resources_folder) if file.startswith('paraphrase') and file.endswith('.pkl')]
        for file in sorted(files):
            records+=FileIO.read_pickle(self.resources_folder/file)
        feedback_file = self.resources_folder/'paraphrases-feedback.json'

        self.paraphrases_content_manager = ContentManager(
            DataClassDataProvider(records),
            feedback_file,
            self.content_strategy
        )

    def _paraphrase_utterance(self, u: Utterance, info: TextInfo) -> Utterance:
        if self.paraphrases_content_manager is None:
            return u
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
        state_tag = copy(self.state.__dict__)
        if 'language' in state_tag:
            del state_tag['language']
        matcher = self.paraphrases_content_manager.match().strong(template_tag).weak(state_tag)
        #matcher.debug = True
        template_record = matcher.find_content()
        if template_record is None:
            return u
        self.paraphrases_content_manager.feedback(template_record.filename, 'seen')
        self.last_content_id = template_record.filename
        return template_record.template(u.value)

    @message_handler
    def paraphrase(self, text: PlayableTextMessage[UtteranceSequenceCommand]) -> PlayableTextMessage[UtteranceSequenceCommand]:
        if not isinstance(text.text, UtteranceSequenceCommand):
            return text.with_new_envelop().as_propagation_confirmation_to(text)
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

