from typing import Iterable, Callable, Optional
from .categories import DeCasus, DeGenus, DeNumerus, DeArticleType
from .word_tools import DeWordTools
from ..common import WordProcessor


# ---------------------------------------------------------------------------
# Adjective ending tables [article_type][numerus][genus][casus]
# Plural endings are identical for all genders; all three genus keys carry
# the same value so callers need not special-case plural.
# ---------------------------------------------------------------------------

_S = DeNumerus.SINGULAR
_P = DeNumerus.PLURAL
_M = DeGenus.MASKULINUM
_F = DeGenus.FEMININUM
_N = DeGenus.NEUTRUM
_NOM = DeCasus.NOMINATIV
_GEN = DeCasus.GENITIV
_DAT = DeCasus.DATIV
_AKK = DeCasus.AKKUSATIV

ADJECTIVE_ENDINGS: dict[DeArticleType, dict] = {
    DeArticleType.STRONG: {
        _S: {
            _M: {_NOM: 'er', _GEN: 'en', _DAT: 'em', _AKK: 'en'},
            _F: {_NOM: 'e',  _GEN: 'er', _DAT: 'er', _AKK: 'e'},
            _N: {_NOM: 'es', _GEN: 'en', _DAT: 'em', _AKK: 'es'},
        },
        _P: {
            _M: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
            _F: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
            _N: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
        },
    },
    DeArticleType.WEAK: {
        _S: {
            _M: {_NOM: 'e',  _GEN: 'en', _DAT: 'en', _AKK: 'en'},
            _F: {_NOM: 'e',  _GEN: 'en', _DAT: 'en', _AKK: 'e'},
            _N: {_NOM: 'e',  _GEN: 'en', _DAT: 'en', _AKK: 'e'},
        },
        _P: {
            _M: {_NOM: 'en', _GEN: 'en', _DAT: 'en', _AKK: 'en'},
            _F: {_NOM: 'en', _GEN: 'en', _DAT: 'en', _AKK: 'en'},
            _N: {_NOM: 'en', _GEN: 'en', _DAT: 'en', _AKK: 'en'},
        },
    },
    DeArticleType.MIXED: {
        _S: {
            _M: {_NOM: 'er', _GEN: 'en', _DAT: 'en', _AKK: 'en'},
            _F: {_NOM: 'e',  _GEN: 'en', _DAT: 'en', _AKK: 'e'},
            _N: {_NOM: 'es', _GEN: 'en', _DAT: 'en', _AKK: 'es'},
        },
        # MIXED plural → grammatically correct absence of article; use STRONG endings
        _P: {
            _M: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
            _F: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
            _N: {_NOM: 'e',  _GEN: 'er', _DAT: 'en', _AKK: 'e'},
        },
    },
}

# ---------------------------------------------------------------------------
# Article tables
# ---------------------------------------------------------------------------

# Definite articles (WEAK declension)
DEFINITE_ARTICLES: dict[DeNumerus, dict[DeGenus, dict[DeCasus, str]]] = {
    _S: {
        _M: {_NOM: 'der', _GEN: 'des', _DAT: 'dem', _AKK: 'den'},
        _F: {_NOM: 'die', _GEN: 'der', _DAT: 'der', _AKK: 'die'},
        _N: {_NOM: 'das', _GEN: 'des', _DAT: 'dem', _AKK: 'das'},
    },
    _P: {
        _M: {_NOM: 'die', _GEN: 'der', _DAT: 'den', _AKK: 'die'},
        _F: {_NOM: 'die', _GEN: 'der', _DAT: 'den', _AKK: 'die'},
        _N: {_NOM: 'die', _GEN: 'der', _DAT: 'den', _AKK: 'die'},
    },
}

# Indefinite articles (MIXED declension, singular only)
INDEFINITE_ARTICLES: dict[DeGenus, dict[DeCasus, str]] = {
    _M: {_NOM: 'ein',   _GEN: 'eines', _DAT: 'einem', _AKK: 'einen'},
    _F: {_NOM: 'eine',  _GEN: 'einer', _DAT: 'einer', _AKK: 'eine'},
    _N: {_NOM: 'ein',   _GEN: 'eines', _DAT: 'einem', _AKK: 'ein'},
}

_CASUS_KEY = {
    DeCasus.NOMINATIV: 'nominativ',
    DeCasus.GENITIV:   'genitiv',
    DeCasus.DATIV:     'dativ',
    DeCasus.AKKUSATIV: 'akkusativ',
}
_NUMERUS_KEY = {
    DeNumerus.SINGULAR: 'singular',
    DeNumerus.PLURAL:   'plural',
}
_GENUS_FROM_STR = {'m': DeGenus.MASKULINUM, 'f': DeGenus.FEMININUM, 'n': DeGenus.NEUTRUM}


class DeDeclinator:

    @staticmethod
    def inflect_noun(word: str, casus: DeCasus, numerus: DeNumerus) -> str:
        entry = DeWordTools.get_noun_entry(word)
        if entry is None:
            return word
        key = f'{_CASUS_KEY[casus]} {_NUMERUS_KEY[numerus]}'
        return entry['flexion'].get(key, word)

    @staticmethod
    def get_noun_genus(word: str) -> DeGenus | None:
        entry = DeWordTools.get_noun_entry(word)
        if entry is None:
            return None
        return _GENUS_FROM_STR.get(entry.get('genus'))

    @staticmethod
    def inflect_adjective(
            word: str,
            casus: DeCasus,
            genus: DeGenus,
            numerus: DeNumerus,
            article_type: DeArticleType,
    ) -> str:
        stem = DeWordTools.get_lemma(word)
        ending = ADJECTIVE_ENDINGS[article_type][numerus][genus][casus]
        return stem + ending

    @staticmethod
    def choose_words_to_inflect(words: list[str]) -> list[int]:
        """
        Return indices of all adjectives in base form that precede the first noun,
        plus the index of that first noun itself. Stops after the first noun.
        """
        result = []
        for i, word in enumerate(words):
            if DeWordTools.is_noun(word):
                result.append(i)
                break
            if DeWordTools.is_adjective_in_base_form(word):
                result.append(i)
        return result

    @staticmethod
    def get_article(
            casus: DeCasus,
            genus: DeGenus,
            numerus: DeNumerus,
            article_type: DeArticleType,
    ) -> str | None:
        """
        Return the article string to prepend, or None if no article is needed.
        MIXED + PLURAL → no article (grammatically correct absence).
        """
        if article_type == DeArticleType.STRONG:
            return None
        if article_type == DeArticleType.WEAK:
            return DEFINITE_ARTICLES[numerus][genus][casus]
        # MIXED
        if numerus == DeNumerus.PLURAL:
            return None  # grammatically correct: no article for indef. plural
        return INDEFINITE_ARTICLES[genus][casus]

    @staticmethod
    def _effective_article_type(article_type: DeArticleType, numerus: DeNumerus) -> DeArticleType:
        """MIXED + PLURAL uses STRONG adjective endings (no article)."""
        if article_type == DeArticleType.MIXED and numerus == DeNumerus.PLURAL:
            return DeArticleType.STRONG
        return article_type

    @staticmethod
    def declinate(
            text: str,
            casus: DeCasus | None = None,
            genus: DeGenus | None = None,
            numerus: DeNumerus | None = None,
            article_type: DeArticleType | None = None,
            word_selector: Optional[Callable[[list[str]], Iterable[int]]] = None,
    ) -> str:
        if casus is None and genus is None and numerus is None:
            return text

        casus = casus or DeCasus.NOMINATIV
        numerus = numerus or DeNumerus.SINGULAR
        article_type = article_type or DeArticleType.STRONG
        adj_article_type = DeDeclinator._effective_article_type(article_type, numerus)

        if word_selector is None:
            word_selector = DeDeclinator.choose_words_to_inflect

        fragments = WordProcessor.word_split(text)
        words: list[str] = []
        word_to_fragment: dict[int, int] = {}
        all_texts: list[str] = []

        for idx, f in enumerate(fragments):
            if f.is_word:
                word_to_fragment[len(words)] = idx
                words.append(f.fragment)
            all_texts.append(f.fragment)

        # Auto-detect genus from the first capitalized noun in the phrase.
        # Only check capitalized words — German nouns are always capitalized,
        # so this avoids false matches on adjectives like "kleine" hitting
        # "Kleine" (feminine) in the dictionary.
        effective_genus = genus
        if effective_genus is None:
            for word in words:
                if word and word[0].isupper():
                    g = DeDeclinator.get_noun_genus(word)
                    if g is not None:
                        effective_genus = g
                        break
        if effective_genus is None:
            effective_genus = DeGenus.MASKULINUM

        selected = list(word_selector(words))
        for wi in selected:
            word = words[wi]
            if DeWordTools.is_noun(word):
                all_texts[word_to_fragment[wi]] = DeDeclinator.inflect_noun(word, casus, numerus)
            else:
                all_texts[word_to_fragment[wi]] = DeDeclinator.inflect_adjective(
                    word, casus, effective_genus, numerus, adj_article_type
                )

        result = ''.join(all_texts)

        article = DeDeclinator.get_article(casus, effective_genus, numerus, article_type)
        if article is not None:
            result = article + ' ' + result

        return result
