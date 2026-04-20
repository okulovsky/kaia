from enum import Enum


class DeCasus(Enum):
    NOMINATIV = 'nominativ'
    GENITIV = 'genitiv'
    DATIV = 'dativ'
    AKKUSATIV = 'akkusativ'


class DeGenus(Enum):
    MASKULINUM = 'masc'
    FEMININUM = 'fem'
    NEUTRUM = 'neut'


class DeNumerus(Enum):
    SINGULAR = 'singular'
    PLURAL = 'plural'


class DeArticleType(Enum):
    STRONG = 'strong'   # no article (starke Deklination)
    WEAK = 'weak'       # after definite article der/die/das (schwache Deklination)
    MIXED = 'mixed'     # after indefinite article ein/kein/mein (gemischte Deklination)
