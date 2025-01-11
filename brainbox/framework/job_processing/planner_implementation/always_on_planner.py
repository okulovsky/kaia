from ..planner import IPlanner, PlannerArguments, StartCommand, AssignAction, IPlannerAction
from typing import Union

class AlwaysOnPlanner(IPlanner):
    Mode = StartCommand.Mode
    def __init__(self, mode: Union['AlwaysOnPlanner.Mode',None] = None):
        if mode is None:
            mode = AlwaysOnPlanner.Mode.FindThenStart
        self.mode = mode

    def plan(self, arguments: PlannerArguments) -> list[IPlannerAction]:
        available = {op.key:op for op in arguments.deciders}
        result = []
        for job in arguments.non_finished_tasks:
            if job.assigned:
                continue
            key = job.get_decider_instance_key()
            if key in available:
                result.append(AssignAction(job.id, available[key].instance_id, key))
                continue
            else:
                result.append(StartCommand(key, self.mode))
        return result

