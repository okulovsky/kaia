from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from ..core import JobForPlanner, OperatorStateForPlanner, OperatorLogHandle, OperatorLogItem
from .planner_action import IPlannerAction





@dataclass
class PlannerArguments:
    non_finished_tasks: tuple[JobForPlanner,...]
    deciders: tuple[OperatorStateForPlanner,...]
    log_handler: OperatorLogHandle = field(default_factory=lambda:OperatorLogHandle(None,OperatorLogItem.Level.Planer,None))


class IPlanner(ABC):
    @abstractmethod
    def plan(self, arguments: PlannerArguments) -> list[IPlannerAction]:
        pass