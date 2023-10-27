from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .job import BrainBoxJob
from .decider_instance import DeciderState

class IPlanner(ABC):
    @dataclass
    class Response:
        assign_tasks: Optional[Tuple[str,...]] = None
        warm_up: Optional[Tuple[str,...]] = None
        cool_down: Optional[Tuple[str,...]] = None

    @abstractmethod
    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJob],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        pass