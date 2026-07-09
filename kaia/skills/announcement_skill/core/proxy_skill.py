from dataclasses import dataclass
from abc import abstractmethod

from avatar.daemon import IntentsPack
from grammatron import Template, TemplateBase
from ....assistant import IKaiaSkill
from typing import Iterable

@dataclass
class ProxySkill(IKaiaSkill):
    @abstractmethod
    def get_inner_skills(self) -> Iterable[IKaiaSkill]:
        pass

    def _unique(self, array, selector):
        result = []
        seen = set()
        for item in array:
            key = selector(item)
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    def get_intents(self) -> Iterable[Template]:
        intents = []
        for skill in self.get_inner_skills():
            intents.extend(skill.get_intents())
        return self._unique(intents, lambda z: z.get_name())

    def get_replies(self) -> Iterable[TemplateBase]:
        replies = []
        for skill in self.get_inner_skills():
            replies.extend(skill.get_replies())
        return self._unique(replies, lambda z: z.get_name())

    def get_extended_intents_packs(self) -> Iterable[IntentsPack]:
        packs = []
        for skill in self.get_inner_skills():
            packs.extend(skill.get_extended_intents_packs())
        return self._unique(packs, lambda z: z.name)
