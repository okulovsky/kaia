from ..planner import IPlanner, PlannerArguments, StartCommand, AssignAction, IPlannerAction


class AlwaysOnPlanner(IPlanner):
    def __init__(self, find_instead_of_starting: bool = True):
        self.find_instead_of_starting = find_instead_of_starting

    def plan(self, arguments: PlannerArguments) -> list[IPlannerAction]:
        available = {op.key:op for op in arguments.deciders if op.up}
        result = []
        for job in arguments.non_finished_tasks:
            if job.assigned:
                continue
            key = job.get_decider_instance_key()
            if key in available:
                result.append(AssignAction(job.id, available[key].instance_id, key))
                continue
            else:
                result.append(StartCommand(key, self.find_instead_of_starting))
        return result

