from typing import *
from abc import ABC, abstractmethod
from kaia.dub.core import Template, Utterance, TemplatesCollection, IntentsPack
from enum import Enum

class IKaiaSkill(ABC):
    class Type(Enum):
        SingleLine = 0
        MultiLine = 1


    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_runner(self):
        pass

    @abstractmethod
    def get_type(self) -> 'IKaiaSkill.Type':
        pass

    def get_intents(self) -> Iterable[Template]:
        return []

    def get_replies(self) -> Iterable[Template]:
        return []

    def should_start(self, input) -> bool:
        return False

    def should_proceed(self, input) -> bool:
        return False

    def get_extended_intents_packs(self) -> Iterable[IntentsPack]:
        return []


class KaiaSkillBase(IKaiaSkill):
    def __init__(self,
                 intents_class: Optional[Type[TemplatesCollection]] = None,
                 replies_class: Optional[Type[TemplatesCollection]] = None,
                 name: Optional[str] = None,
                 ):
        self._name = name if name is not None else type(self).__name__
        self._intents = intents_class.get_templates() if intents_class is not None else []
        self._dubs = replies_class.get_templates() if replies_class is not None else []
        self._intents_names = set(i.name for i in self._intents)

    @abstractmethod
    def run(self):
        pass

    def get_name(self) -> str:
        return self._name

    def get_runner(self):
        return self.run

    def get_intents(self) -> Iterable[Template]:
        return self._intents

    def get_replies(self) -> Iterable[Template]:
        return self._dubs


class SingleLineKaiaSkill(KaiaSkillBase):
    def __init__(self,
                 intents_class: Optional[Type[TemplatesCollection]] = None,
                 replies_class: Optional[Type[TemplatesCollection]] = None,
                 name: Optional[str] = None,
                 ):
        super().__init__(intents_class, replies_class, name)

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.SingleLine

    def should_start(self, input) -> False:
        if isinstance(input, Utterance):
            return input.template.name in self._intents_names
        return False
