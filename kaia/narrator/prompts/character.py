from typing import *
from dataclasses import dataclass
from kaia.dub.core import IPredefinedField, IDubBinding, ToStrDub
from enum import Enum


@dataclass
class Character:
    class Gender(Enum):
        Feminine = 0
        Masculine = 1
        Neutral = 2

    name: str
    gender: Gender


class PronounDubBinding(IDubBinding):
    def __init__(self, case: int, fields: Iterable[str]):
        self._case = case
        self._fields = tuple(fields)

    @property
    def type(self):
        return ToStrDub()

    @property
    def name(self):
        return 'pronoun__' + '_'.join(self._fields) + f'__case{self._case}'

    def get_consumed_keys(self) -> Tuple[str, ...]:
        return self._fields

    @property
    def produces_value(self):
        return False

    def get_value_to_consume(self, d):
        characters = [d[field] for field in self._fields if field in d and d[field] is not None]
        if len(characters) == 0:
            raise ValueError(f"No fields of {self._fields} are available")
        if len(characters) > 1:
            return ['they', 'them', 'their', 'themselves'][self._case]
        c: Character = d[self._fields[0]]
        if c.gender == Character.Gender.Feminine:
            return ['she', 'her', 'her', 'herself'][self._case]
        elif c.gender == Character.Gender.Masculine:
            return ['he', 'him', 'his', 'himself'][self._case]
        else:
            return ['it', 'it', 'its', 'itself'][self._case]

    def set_produced_value(self, value, d) -> None:
        pass


class CharacterDubBinding(IDubBinding):
    def __init__(self, fields):
        self._fields = tuple(fields)

    @property
    def type(self):
        return ToStrDub()

    @property
    def name(self):
        return 'character__' + '_'.join(self._fields)

    def get_consumed_keys(self) -> Tuple[str, ...]:
        return self._fields

    def produces_value(self) -> bool:
        return False

    def get_value_to_consume(self, d: Dict) -> Any:
        names = [d[field].name for field in self._fields if field in d and d[field] is not None]
        if len(names) == 0:
            raise ValueError(f"No fields of {self._fields} are available")
        elif len(names) == 1:
            return names[0]
        else:
            return ', '.join(names[:-1]) + ' and ' + names[-1]

    def set_produced_value(self, value, d: Dict) -> None:
        pass


class PronounPredefinedField(IPredefinedField):
    def __init__(self, case, fields):
        self.fields = fields
        self.case = case

    def get_dub(self):
        return PronounDubBinding(self.case, self.fields)

    def get_name(self) -> str:
        return self.get_dub().name


class PronounsPack:
    def __init__(self, fields):
        self.fields = fields

    @property
    def subjective(self):
        return PronounPredefinedField(0, self.fields)

    @property
    def objective(self):
        return PronounPredefinedField(1, self.fields)

    @property
    def possessive(self):
        return PronounPredefinedField(2, self.fields)

    @property
    def reflexive(self):
        return PronounPredefinedField(3, self.fields)


class CharacterPredefinedField(IPredefinedField):
    def __init__(self, fields: tuple[str, ...]):
        self._fields = fields

    def get_dub(self):
        return CharacterDubBinding(self._fields)

    def get_name(self) -> str:
        return self.get_dub().name

    @property
    def pronoun(self) -> PronounsPack:
        return PronounsPack(self._fields)


class CharacterWorldField(CharacterPredefinedField):
    def __init__(self, field: str):
        super().__init__((field,))

    @property
    def field_name(self) -> str:
        return self._fields[0]