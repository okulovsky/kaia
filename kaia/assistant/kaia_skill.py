from typing import *
from abc import ABC, abstractmethod
from grammatron import Template, Utterance, TemplatesCollection
from avatar.daemon import IntentsPack
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

    ACCEPTS_ANY_LANGUAGE = 'ANY_LANGUAGE'

    def get_language(self) -> str|None:
        return None

    def get_extended_intents_packs(self) -> Iterable[IntentsPack]:
        return []


def _class_to_intent_collection(c) -> tuple[Template,...]:
    if c is None:
        return ()
    if isinstance(c, type):
        if issubclass(c, TemplatesCollection):
            return tuple(c.get_templates())
        else:
            raise ValueError(f"If type, must be TemplatesCollection, but was {c}")
    try:
        l = tuple(c)
    except Exception as ex:
        raise ValueError("If not type, expected to be iterable of Templates") from ex
    for index, element in enumerate(l):
        if not isinstance(element, Template):
            raise ValueError(f"If iterable, expect to contain only Templates, but at index {index} was\n{element}")
    return l


class KaiaSkillBase(IKaiaSkill):
    def __init__(self,
                 intents_class: Union[Type[TemplatesCollection], Iterable[Template],None] = None,
                 replies_class: Union[Type[TemplatesCollection], Iterable[Template],None] = None,
                 name: Optional[str] = None,
                 ):
        self._name = name if name is not None else type(self).__name__
        self._intents = _class_to_intent_collection(intents_class)
        self._dubs = _class_to_intent_collection(replies_class)
        self._intents_names = set(i.get_name() for i in self._intents)

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

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine


class SingleLineKaiaSkill(KaiaSkillBase):
    def __init__(self,
                 intents_class: Union[Type[TemplatesCollection], Iterable[Template], None] = None,
                 replies_class: Union[Type[TemplatesCollection], Iterable[Template], None] = None,
                 name: Optional[str] = None,
                 ):
        super().__init__(intents_class, replies_class, name)

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.SingleLine

    def should_start(self, input) -> False:
        if isinstance(input, Utterance):
            return input.template.get_name() in self._intents_names
        return False
