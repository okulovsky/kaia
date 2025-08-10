import inflect
import lemminflect
from ..common import WordProcessor

class EnglishWordTools:
    inflect_engine = inflect.engine()

    @staticmethod
    def get_noun_vocabulary_form(word: str) -> str|None:
        lemmas = lemminflect.getAllLemmas(word)
        if 'NOUN' not in lemmas:
            return None
        if len(lemmas['NOUN']) == 0:
            return None
        return lemmas['NOUN'][0]

    @staticmethod
    def word_to_plural(word: str) -> str:
        return EnglishWordTools.inflect_engine.plural(word)

    @staticmethod
    def text_to_plural(phrase: str) -> str:
        words = WordProcessor.word_split(phrase)
        for w in words:
            if w.is_word:
                lemma = EnglishWordTools.get_noun_vocabulary_form(w.fragment)
                if lemma == w.fragment:
                    w.fragment = EnglishWordTools.word_to_plural(lemma)
                    break
        entity_text = ''.join(w.fragment for w in words)
        return entity_text
