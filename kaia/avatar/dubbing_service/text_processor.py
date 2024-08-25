from kaia.dub import Utterance, UtterancesSequence
import nltk
from dataclasses import dataclass

TextLike = str|Utterance|UtterancesSequence

@dataclass
class TextProcessorOutput:
    full_text: str
    chunks: tuple[str,...]


class TextProcessor:
    def __init__(self):
        try:
            nltk.sent_tokenize('test test')
        except:
            nltk.download('punkt')


    def _to_str_array(self, obj: TextLike):
        if isinstance(obj, str):
            return [obj]
        if isinstance(obj, Utterance):
            return [obj.to_str()]
        if isinstance(obj, UtterancesSequence):
            return [u.to_str() for u in obj.utterances]

    def _prettify_utterance_string(self, s: str):
        s = s.strip()
        s = s[0].upper() + s[1:]
        if s[-1] not in {'.','!','?'}:
            s+='.'
        return s

    def process(self, obj: TextLike):
        parts = self._to_str_array(obj)
        parts = [self._prettify_utterance_string(s) for s in parts]
        full_text = ' '.join(parts)
        sentences = nltk.sent_tokenize(full_text)
        return TextProcessorOutput(full_text, tuple(sentences))






