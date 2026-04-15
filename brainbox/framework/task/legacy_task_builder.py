from foundation_kaia.marshalling import JSON
from foundation_kaia.marshalling.reflector import DeclaredType
from .task import BrainBoxTaskOptionals
from .task_builder import TaskBuilder
from .entry_point import _parse_signatures
from typing import Type, TypeVar

T = TypeVar('T')

class LegacyTaskBuilder:
    @staticmethod
    def call(decider_type: Type[T], *, parameter: str|None = None, id: str|None = None, batch: str|None = None, info: JSON = None) -> T:
        dt = DeclaredType.parse(decider_type)
        _signatures = _parse_signatures(dt, decider_type.__name__, [], service_only=False)
        instance = TaskBuilder()
        instance._signatures = _signatures
        instance._optionals = BrainBoxTaskOptionals(id, parameter, batch, info)
        instance._after_others = []
        return instance
