from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ..small_classes import DeciderState, DeciderInstanceSpec
from .brain_box_job_for_planner import BrainBoxJobForPlanner





class IPlanner(ABC):
    @dataclass
    class Response:
        assign_tasks: Optional[Tuple[str,...]] = None
        warm_up: Optional[Tuple[DeciderInstanceSpec,...]] = None
        cool_down: Optional[Tuple[DeciderInstanceSpec,...]] = None

    @abstractmethod
    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJobForPlanner],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        pass

    def shallow_warmup_only(self, decider_to_warmup: DeciderInstanceSpec, instances: Iterable[DeciderState]):
        return False

    def logout(self, instances: Iterable[DeciderState]):
        return [i.spec for i in instances if i.up]


