from ...scene import SceneHint, Actors
from ...data import Character
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Plan:
    plan: str
    hint: SceneHint

class IPlanFactory(ABC):
    @abstractmethod
    def describe(self, actors: Actors) -> Plan:
        pass

