from typing import *
from .planner import *
from yo_fluq import *
from datetime import datetime

class SimplePlanner(IPlanner):
    def __init__(self,
                 cooldown_delay_in_seconds: Optional[int] = None,
                 datetime_factory: Optional[Callable[[], datetime]] = datetime.now
                 ):
        self.cooldown_delay_in_seconds = cooldown_delay_in_seconds
        self.datetime_factory = datetime_factory
        self.has_cooldown_delay = self.cooldown_delay_in_seconds is not None and self.datetime_factory is not None
        self.last_cooldown_flag: Optional[datetime] = None

    def _cooldown_respecting_delay(self, spec):
        if not self.has_cooldown_delay:
            return IPlanner.Response(None, None, (spec,))
        now = self.datetime_factory()
        if self.last_cooldown_flag is None:
            self.last_cooldown_flag = now
            return IPlanner.Response(None, None, None)
        delta = (now - self.last_cooldown_flag).total_seconds()
        if delta < self.cooldown_delay_in_seconds:
            return IPlanner.Response(None, None, None)
        return IPlanner.Response(None, None, (spec,))


    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJobForPlanner],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        non_finished_tasks = list(non_finished_tasks)

        active_service = Query.en(instances).where(lambda z: z.up).single_or_default()

        if active_service is None:
            service_to_activate: List[DeciderInstanceSpec] = (Query
                        .en(non_finished_tasks)
                        .group_by(lambda z: z.get_decider_instance_spec())
                        .select(lambda z: (z.key, len(z.value)))
                        .order_by_descending(lambda z: z[1])
                        .then_by(lambda z: str(z[0]))
                        .select(lambda z: z[0])
                        .to_list()
                        )
            if len(service_to_activate) == 0:
                return IPlanner.Response(None, None, None)
            else:
                return IPlanner.Response(None, (service_to_activate[0],), None)

        tasks_for_active_service = Query.en(non_finished_tasks).where(lambda z: z.get_decider_instance_spec()==active_service.spec).to_list()
        if len(tasks_for_active_service) == 0:
            if len(non_finished_tasks) > 0: #
                return IPlanner.Response(None, None, (active_service.spec,))
            return self._cooldown_respecting_delay(active_service.spec)

        currently_at_active_service = Query.en(tasks_for_active_service).where(lambda z: z.assigned).count()
        if currently_at_active_service >= 2:
            return IPlanner.Response(None, None, None)

        next = (
            Query
            .en(tasks_for_active_service)
            .where(lambda z: not z.assigned)
            .order_by(lambda z: z.ordering_token)
            .then_by(lambda z: z.received_timestamp)
            .first_or_default()
        )

        if next is None:
            return IPlanner.Response(None, None, None)

        return IPlanner.Response((next.id,), None, None)








