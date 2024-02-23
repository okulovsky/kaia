from .multi_decider_planner import *

class SmartPlanner(MultiDeciderPlanner):
    def __init__(self,
                 heavy_load_services: Iterable[str],
                 max_waiting_new_task_before_going_down_in_minutes: Optional[int] = None
                 ):
        self.heavy_load_services = set(heavy_load_services)
        self.max_waiting_new_task_before_going_down_in_minutes = max_waiting_new_task_before_going_down_in_minutes

    def _default_behaviour(self, stats: PlanerStats):
        up = self.up_the_required_deciders(stats)
        up = tuple(x for x in up if x.decider_name not in self.heavy_load_services)
        assign = self.assign_tasks_to_active_deciders(stats)
        return IPlanner.Response(assign, up, ())


    def plan_inner(self, planner_stats: PlanerStats) -> 'IPlanner.Response':
        heavy_decider_up_spec: Optional[DeciderInstanceSpec] = None
        heavy_decider_should_down_if_needed = False
        heavy_decider_should_down_regardless = False
        deciders_wanting_up = []

        for spec, stats in planner_stats.deciders_stats.items():
            if spec.decider_name in self.heavy_load_services:
                if stats.up:
                    if heavy_decider_up_spec is not None:
                        raise ValueError(f"Heavy deciders {heavy_decider_up_spec.decider_name} and {spec.decider_name} are both up")
                    heavy_decider_up = True
                    heavy_decider_up_spec = spec
                    if len(stats.total_tasks) == 0:
                        heavy_decider_should_down_if_needed = True
                        if self.max_waiting_new_task_before_going_down_in_minutes and self.max_waiting_new_task_before_going_down_in_minutes > stats.last_interaction_minutes_ago:
                            heavy_decider_should_down_regardless = True
                else:
                    if len(stats.total_tasks) > 0:
                        deciders_wanting_up.append(spec)

        #Should we terminate current heavy decider?
        if heavy_decider_up_spec is not None:
            bring_down = heavy_decider_should_down_regardless
            if len(deciders_wanting_up) > 0:
                bring_down = heavy_decider_should_down_if_needed
            if bring_down:
                return IPlanner.Response((), (), (heavy_decider_up_spec,))

        #Heavy decider is up and doesn't want to leave. We can only up non-heavy deciders and assign tasks
        if heavy_decider_up_spec is not None:
            return self._default_behaviour(planner_stats)

        #No heavy decider and no candidate
        if len(deciders_wanting_up) == 0:
            return self._default_behaviour(planner_stats)

        #No heavy decider and there are candidates
        decider_names = set(s.decider_name for s in deciders_wanting_up)
        for task in planner_stats.non_finished_tasks:
            if task.decider in decider_names and not task.assigned:
                return IPlanner.Response((), (task.get_decider_instance_spec(),), ())

