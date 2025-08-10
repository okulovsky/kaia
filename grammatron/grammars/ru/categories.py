from enum import Enum

class RuDeclension(Enum):
    NOMINATIVE = 'nomn'  # именительный
    GENITIVE = 'gent'  # родительный
    DATIVE = 'datv'  # дательный
    ACCUSATIVE = 'accs'  # винительный
    INSTRUMENTAL = 'ablt'  # творительный
    PREPOSITIONAL = 'loct'  # предложный
    PARTITIVE = 'gen2'  # второй родительный (частичный)
    LOCATIVE = 'loc2'  # второй предложный (локатив)
    VOCATIVE = 'voct'  # звательный (редко используется)



class RuGender(Enum):
    MASCULINE = 'masc'  # мужской
    FEMININE = 'femn'  # женский
    NEUTER = 'neut'  # средний
    COMMON = 'Ms-f'  # общий род (например, "умница")


class RuNumber(Enum):
    SINGULAR = 'sing'  # единственное число
    PLURAL = 'plur'  # множественное число