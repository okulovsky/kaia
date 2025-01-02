from ..media_library_manager import MediaLibraryManager
from kaia.dub.core.templates.paraphrase import ParaphraseInfo
from kaia.dub import Utterance, UtterancesSequence
from .text_processor import TextLike
from dataclasses import dataclass

@dataclass
class ParaphraseServiceSettings:
    manager: MediaLibraryManager
    template_to_paraphrase_tag_name: str


class ParaphraseService:
    def __init__(self, settings: ParaphraseServiceSettings):
        self.settings = settings
        self.last_file_id: str|None = None


    def _paraphrase_utterance(self, u: Utterance, state) -> list[Utterance]:
        if u.template.meta.paraphrase is None:
            return [u]
        template_tag = {self.settings.template_to_paraphrase_tag_name: u.template.name}
        content = self.settings.manager.find_content(state, template_tag)
        if content is None:
            return [u]
        self.settings.manager.feedback(content.file_id, 'seen')
        self.last_file_id = content.file_id
        if u.template.meta.paraphrase.type == ParaphraseInfo.Type.After:
            return [u, Utterance.from_string(content.content)]
        elif u.template.meta.paraphrase.type == ParaphraseInfo.Type.Instead:
            return [Utterance.from_string(content.content)]
        else:
            raise ValueError(f'Unknown paraphrase type: {u.template.meta.paraphrase.type}')



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


