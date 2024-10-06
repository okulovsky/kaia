from .planner import *
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DeciderStats:
    up: bool = False
    assigned: List[str] = field(default_factory=lambda: [])
    waiting: List[str] = field(default_factory=lambda: [])
    last_interaction_minutes_ago: Optional[float] = None

    @property
    def total_tasks(self):
        return len(self.assigned) + len(self.waiting)

@dataclass
class PlanerStats:
    non_finished_tasks: Tuple[BrainBoxJobForPlanner]
    deciders_stats: Dict[DeciderInstanceSpec, DeciderStats]



class MultiDeciderPlanner(IPlanner):
    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJobForPlanner],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        stats: Dict[DeciderInstanceSpec,DeciderStats] = {}
        current_time = datetime.now()
        for task in non_finished_tasks:
            spec = task.get_decider_instance_spec()
            if spec not in stats:
                stats[spec] = DeciderStats()
            if task.assigned:
                stats[spec].assigned.append(task.id)
            else:
                stats[spec].waiting.append(task.id)
            interaction_time = task.received_timestamp
            delta = (current_time - interaction_time).total_seconds()/60
            if stats[spec].last_interaction_minutes_ago is None or stats[spec].last_interaction_minutes_ago > delta:
                stats[spec].last_interaction_minutes_ago = delta
        for instance in instances:
            if instance.spec not in stats:
                stats[instance.spec] = DeciderStats()
            stats[instance.spec].up = instance.up

        planner_stats = PlanerStats(tuple(non_finished_tasks), stats)
        return self.plan_inner(planner_stats)

    def assign_tasks_to_active_deciders(self, planner_stats: PlanerStats, max_assigned_tasks: int = 2):
        assign = []
        for spec, stats in planner_stats.deciders_stats.items():
            if stats.up:
                if len(stats.assigned) < max_assigned_tasks and len(stats.waiting) > 0:
                    assign.append(stats.waiting[0])
        return tuple(assign)

    def up_the_required_deciders(self, stats: PlanerStats):
        up = []
        for spec, stats in stats.deciders_stats.items():
            if not stats.up:
                if stats.total_tasks > 0:
                    up.append(spec)
        return tuple(up)



    def plan_inner(self, stats: PlanerStats) -> 'IPlanner.Response':
        pass


class AlwaysOnPlanner(MultiDeciderPlanner):
    def __init__(self, shallow_warmup_only: bool = True):
        self._shallow_warmup_only = shallow_warmup_only

    def plan_inner(self, stats: PlanerStats) -> 'IPlanner.Response':
        assign = self.assign_tasks_to_active_deciders(stats)
        up = self.up_the_required_deciders(stats)
        return IPlanner.Response(assign, up, ())

    def logout(self, instances: Iterable[DeciderState]):
        return []

    def shallow_warmup_only(self, decider_to_warmup: DeciderInstanceSpec, instances: Iterable[DeciderState]):
        return self._shallow_warmup_only









