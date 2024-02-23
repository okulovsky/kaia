from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ..small_classes import BrainBoxJob, DeciderState, DeciderInstanceSpec

class IPlanner(ABC):
    @dataclass
    class Response:
        assign_tasks: Optional[Tuple[str,...]] = None
        warm_up: Optional[Tuple[DeciderInstanceSpec,...]] = None
        cool_down: Optional[Tuple[DeciderInstanceSpec,...]] = None

    @abstractmethod
    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJob],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        pass