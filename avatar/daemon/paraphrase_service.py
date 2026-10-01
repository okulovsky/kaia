import os
from typing import *

from grammatron import Utterance, UtterancesSequence, TemplateDub, Template, LanguageDispatchDub
from dataclasses import dataclass

from . import InternalTextCommand
from .common.content import ContentFinder, IRecord, FileFeedbackStorage, IFeedbackStorage
from .common import State, AvatarService, message_handler, InitializationEvent, TextCommand
from copy import copy
from yo_fluq import FileIO

@dataclass
class ParaphraseRecord(IRecord):
    filename: str
    template: Template
    original_template_name: str
    used_variables_tag: str
    language: str
    character: str|None = None
    user: str|None = None

    def get_id(self) -> str:
        return self.filename

    def get_tags(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if key != 'filename'}

    @staticmethod
    def create_variables_tag(variables: Iterable[str]):
        return ','.join(sorted(set(variables)))

    def exact_match_values(self):
        return (self.original_template_name, self.used_variables_tag, self.character, self.user)



class ParaphraseService(AvatarService):
    FEEDBACK_FILENAME = 'paraphrases-feedback.json'
    PARAPHRASES_PREFIX='paraphrase'
    PARAPHRASES_SUFFIX='.pkl'

    def __init__(self, state: State, finder: ContentFinder|None = None):
        self.state = state
        self.finder = finder if finder is not None else ContentFinder()
        self.records: list[ParaphraseRecord]|None = None
        self.feedback_storage: IFeedbackStorage|None = None


    @message_handler
    def on_initialize(self, message: InitializationEvent) -> None:
        records = []
        if not self.resources_folder.is_dir():
            os.makedirs(self.resources_folder)
        files = os.listdir(str(self.resources_folder))
        files = [file for file in files
                 if file.startswith(ParaphraseService.PARAPHRASES_PREFIX)
                 and file.endswith(ParaphraseService.PARAPHRASES_SUFFIX)]

        for file in sorted(files):
            records+=FileIO.read_pickle(self.resources_folder/file)
        self.records = records
        self.feedback_storage = FileFeedbackStorage(self.resources_folder/ParaphraseService.FEEDBACK_FILENAME)

    def _paraphrase_utterance(self, u: Utterance, command: InternalTextCommand) -> Utterance:
        if self.records is None:
            return u
        if not isinstance(u, Utterance):
            return u
        if u.template.get_context() is None:
            return u
        dub = u.template.dub
        language = command.language
        if not isinstance(dub, LanguageDispatchDub):
            return u
        if language not in dub.dispatch:
            return u
        dub = dub.dispatch[language]
        if not isinstance(dub, TemplateDub):
            return u

        variables = dub.find_required_variables(u.value)
        variables_tag = ParaphraseRecord.create_variables_tag(variables)

        state_tag = copy(self.state.__dict__)
        state_tag['language'] = language
        state_tag['character'] = command.character
        state_tag['user'] = command.user

        template_tag = {
            'original_template_name': u.template.get_name(),
            'used_variables_tag': variables_tag,
            'language': language,
            'character': command.character,
        }

        template_record = self.finder.find(
            self.records,
            self.feedback_storage.load(),
            strong=template_tag,
            weak=state_tag,
        )
        if template_record is None:
            return u
        self.feedback_storage.append(template_record.filename, {'seen': 1})
        self.last_content_id = template_record.filename
        return template_record.template(u.value)

    @message_handler
    def paraphrase(self, command: InternalTextCommand) -> InternalTextCommand:
        if isinstance(command.text, str):
            return command.with_new_envelop().as_propagation_confirmation_to(command)
        elif isinstance(command.text, UtterancesSequence):
            sequences = command.text.utterances
        elif isinstance(command.text, Utterance):
            sequences = [command.text]
        else:
            raise ValueError("TextCommand must have str, Utterance, or UtterancesSequence as `text`")
        paraphrase = []
        for u in sequences:
            paraphrase.append(self._paraphrase_utterance(u, command))
        return InternalTextCommand(
            UtterancesSequence(*paraphrase),
            command.user,
            command.language,
            command.character
        ).as_propagation_confirmation_to(command)

    def requires_brainbox(self):
        return False

