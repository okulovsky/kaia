from __future__ import annotations
from chara.common.descriptions.characters.pronouns import Pronouns
from chara import Character
from typing import Union, Iterable
import random

class CharacterReference:
    def __init__(self, *characters: 'Union[Character|CharacterReference|Iterable[Character]]'):
        store = []
        for index, c in enumerate(characters):
            if isinstance(c, Character):
                store.append(c)
            elif isinstance(c, CharacterReference):
                store.extend(c.many)
            else:
                for index_2, cc in enumerate(c):
                    if not isinstance(cc, Character):
                        raise TypeError(f'Expected a Character, got {cc} at argument #{index}, index #{index_2}')
                    store.append(cc)
        self._characters = tuple(store)
        self._junction = 'and'

    def with_junction(self, junction: str):
        result = CharacterReference(*self._characters)
        result._junction = junction
        return result

    @property
    def many(self) -> tuple[Character,...]:
        return self._characters

    @property
    def single(self) -> Character:
        if len(self._characters) == 1:
            return self._characters[0]
        else:
            raise ValueError("CharacterReference references multiple characters")

    def random(self) -> CharacterReference:
        return CharacterReference(random.choice(self._characters))

    @property
    def name(self) -> str:
        if len(self._characters) == 0:
            raise ValueError("CharacterReference references no characters")
        if len(self._characters) == 1:
            return self._characters[0].name
        else:
            return ", ".join([c.name for c in self._characters[:-1]])+" "+self._junction+" "+self._characters[-1].name

    @property
    def pronoun(self) -> Pronouns:
        if len(self._characters) == 0:
            raise ValueError("CharacterReference references no characters")
        return Pronouns(
            self._characters[0].pronoun if len(self._characters) == 1 else None,
            len(self._characters) > 1
        )

    def __add__(self, other: 'CharacterReference|Character|Iterable[Character]') -> 'CharacterReference':
        return CharacterReference(self, other)

    def __sub__(self, other: 'CharacterReference|Character|Iterable[Character]|str|Iterable[str]') -> 'CharacterReference':
        remove = []
        if isinstance(other, (CharacterReference, Character)):
            remove.extend(c.name for c in CharacterReference(other).many)
        elif isinstance(other, str):
            remove.append(other)
        else:
            for index, c in enumerate(other):
                if isinstance(c, Character):
                    remove.append(c.name)
                elif isinstance(c, str):
                    remove.append(c)
                else:
                    raise ValueError(f"Expected str or Character in the iterable, but at index {index} was {c}")
        keep = [c for c in self.many if c.name not in remove]
        return CharacterReference(keep)

    def __iter__(self):
        yield from self.many

    def __contains__(self, item: Character|str|CharacterReference):
        if isinstance(item, Character):
            item = [item.name]
        elif isinstance(item, CharacterReference):
            item = [c.name for c in item]
        elif isinstance(item, str):
            item = [item]
        else:
            raise ValueError(f"Expected str or Character in the iterable, but was {item}")
        existing = {c.name for c in self._characters}
        return all(item in existing for item in item)

    def __len__(self) -> int:
        return len(self._characters)

    def __getitem__(self, item: int) -> Character:
        return self._characters[item]

    def is_(self):
        return self.__str__() + " " + ('is' if len(self._characters) == 1 else 'are') + " "

    def has_(self):
        return self.__str__() + " " + ('has' if len(self._characters) == 1 else 'have') + " "

    def __str__(self):
        return self.name