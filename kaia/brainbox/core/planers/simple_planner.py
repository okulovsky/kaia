from typing import *
from .planner import *
from yo_fluq import *

class SimplePlanner(IPlanner):
    def plan(self,
             non_finished_tasks: Iterable[BrainBoxJob],
             instances: Iterable[DeciderState]
             ) -> 'IPlanner.Response':
        active_service = Query.en(instances).where(lambda z: z.up).single_or_default()

        if active_service is None:
            activate: List[DeciderInstanceSpec] = (Query
                        .en(non_finished_tasks)
                        .where(lambda z: z.ready)
                        .group_by(lambda z: z.get_decider_instance_spec())
                        .select(lambda z: (z.key, len(z.value)))
                        .order_by_descending(lambda z: z[1])
                        .then_by(lambda z: str(z[0]))
                        .select(lambda z: z[0])
                        .to_list()
                        )
            if len(activate) == 0:
                return IPlanner.Response(None, None, None)
            else:
                return IPlanner.Response(None, (activate[0],), None)

        tasks_for_active_service = Query.en(non_finished_tasks).where(lambda z: z.get_decider_instance_spec()==active_service.spec and z.ready).to_list()
        if len(tasks_for_active_service) == 0:
            return IPlanner.Response(None, None, (active_service.spec,))

        currently_at_active_service = Query.en(tasks_for_active_service).where(lambda z: z.assigned).count()
        if currently_at_active_service >= 2:
            return IPlanner.Response(None, None, None)

        next = Query.en(tasks_for_active_service).where(lambda z: not z.assigned).order_by(lambda z: z.received_timestamp).first_or_default()
        if next is None:
            return IPlanner.Response(None, None, None)

        return IPlanner.Response((next.id,), None, None)








