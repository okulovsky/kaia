from typing import *
from abc import ABC, abstractmethod
from ..dub.core import Template, Utterance, TemplatesCollection
import copy

class IAssistantSkill(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_runner(self):
        pass

    def get_intents(self) -> Iterable[Template]:
        return []

    def get_replies(self) -> Iterable[Template]:
        return []

    def should_run_on_input(self, input) -> False:
        return False

    def get_shortcuts(self) -> Dict[str, Utterance]:
        return {}



class AssistantSkill(IAssistantSkill):
    def __init__(self,
                 method: Callable,
                 intents_class: Optional[Type[TemplatesCollection]] = None,
                 replies_class: Optional[Type[TemplatesCollection]] = None,
                 initial_intents: Optional[Iterable[Template]] = None,
                 command_to_intent: Optional[Dict[str,Utterance]] = None,
                 name: Optional[str] = None,
                 ):
        self._method = method
        self._name = name if name is not None else type(self).__name__
        self._intents = intents_class.get_templates() if intents_class is not None else []
        self._dubs = replies_class.get_templates() if replies_class is not None else []

        if initial_intents is None:
            initial_intents = []
        self._initial_intents = set(i.name for i in initial_intents)
        self._command_to_intent = command_to_intent if command_to_intent is not None else {}


    def get_name(self) -> str:
        return self._name

    def get_runner(self):
        return self._method

    def get_intents(self) -> Iterable[Template]:
        return self._intents

    def get_replies(self) -> Iterable[Template]:
        return self._dubs

    def should_run_on_input(self, input) -> False:
        if isinstance(input, str):
            if input in self._command_to_intent:
                input = self._command_to_intent[input]
        if isinstance(input, Utterance):
            return input.template.name in self._initial_intents
        return False

    def get_shortcuts(self) -> Dict[str, Utterance]:
        return copy.copy(self._command_to_intent)
