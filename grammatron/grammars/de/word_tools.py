import simplemma
from german_nouns.lookup import Nouns


class DeWordTools:
    _nouns_db: Nouns | None = None

    @classmethod
    def nouns_db(cls) -> Nouns:
        if cls._nouns_db is None:
            cls._nouns_db = Nouns()
        return cls._nouns_db

    @staticmethod
    def get_lemma(word: str) -> str:
        return simplemma.lemmatize(word, lang='de')

    @staticmethod
    def _noun_entries(word: str) -> list[dict]:
        results = DeWordTools.nouns_db()[word]
        return [
            r for r in results
            if 'Substantiv' in r.get('pos', [])
            and 'adjektivische Deklination' not in r.get('pos', [])  # exclude substantivized adjectives
            and r.get('flexion')
            and r.get('genus') in ('m', 'f', 'n')
        ]

    @staticmethod
    def get_noun_entry(word: str) -> dict | None:
        """Return the first valid noun entry for word, trying lemma as fallback."""
        entries = DeWordTools._noun_entries(word)
        if entries:
            return entries[0]
        lemma = DeWordTools.get_lemma(word)
        if lemma != word:
            entries = DeWordTools._noun_entries(lemma)
            if entries:
                return entries[0]
        return None

    @staticmethod
    def is_noun(word: str) -> bool:
        """Check exact spelling only — no lemma fallback.
        This prevents "kleine" → simplemma → "Kleine" from matching the feminine noun "Kleine".
        Also requires capitalization: German nouns are always written with a capital letter."""
        return bool(word) and word[0].isupper() and bool(DeWordTools._noun_entries(word))

    @staticmethod
    def is_adjective_in_base_form(word: str) -> bool:
        """
        True if the word is a candidate adjective to inflect.
        Heuristic: lowercase (German adjectives are never capitalized like nouns)
        and not a known noun.
        """
        return bool(word) and word[0].islower() and not DeWordTools.is_noun(word)
