from typing import *
from ..planner import IPlanner, PlannerArguments, StartCommand, StopCommand, AssignAction
from ..core import DeciderInstanceKey, OperatorStateForPlanner
from yo_fluq import *
from datetime import datetime

class SimplePlanner(IPlanner):
    def __init__(self,
                 cooldown_delay_in_seconds: int|None = 60*30,
                 datetime_factory: Optional[Callable[[], datetime]] = datetime.now
                 ):
        self.cooldown_delay_in_seconds = cooldown_delay_in_seconds
        self.datetime_factory = datetime_factory
        self.has_cooldown_delay = self.cooldown_delay_in_seconds is not None and self.datetime_factory is not None

    def _cooldown_respecting_delay(self, active_service: OperatorStateForPlanner):
        if not self.has_cooldown_delay:
            return [StopCommand(active_service.instance_id)]
        now = self.datetime_factory()
        delta = (now - active_service.not_busy_since).total_seconds()
        if delta < self.cooldown_delay_in_seconds:
            return []
        return [StopCommand(active_service.instance_id)]

    def _choose_next_decider_to_activate(self, args: PlannerArguments):
        service_to_activate: list[DeciderInstanceKey] = (Query
                    .en(args.non_finished_tasks)
                    .group_by(lambda z: z.get_decider_instance_key())
                    .select(lambda z: (z.key, len(z.value)))
                    .order_by_descending(lambda z: z[1])
                    .then_by(lambda z: str(z[0]))
                    .select(lambda z: z[0])
                    .to_list()
                    )
        if len(service_to_activate) == 0:
            return []
        else:
            args.log_handler.event(f"No active services, starting {service_to_activate[0]}")
            return [StartCommand(service_to_activate[0], StartCommand.Mode.StartOnly)]

    def _get_tasks_for_service(self, args: PlannerArguments, active_service: OperatorStateForPlanner):
        return (
            Query
            .en(args.non_finished_tasks)
            .where(lambda z: z.get_decider_instance_key() == active_service.key)
            .to_list()
        )



    def plan(self, args: PlannerArguments):
        active_service: OperatorStateForPlanner|None = None
        if len(args.deciders) > 1:
            raise ValueError("Simple planner cannot operate with more than 1 decider active")
        elif len(args.deciders) == 1:
            active_service = args.deciders[0]

        if active_service is None:
            return self._choose_next_decider_to_activate(args)

        tasks_for_active_service = self._get_tasks_for_service(args, active_service)
        currently_at_active_service = Query.en(tasks_for_active_service).where(lambda z: z.assigned).to_list()
        next_for_active_service = (
            Query
            .en(tasks_for_active_service)
            .where(lambda z: not z.assigned)
            .order_by(lambda z: z.ordering_token)
            .then_by(lambda z: z.received_timestamp)
            .to_list()
        )

        if len(tasks_for_active_service) == 0:
            if len(args.non_finished_tasks) > 0:
                args.log_handler.event("No tasks for active service, there are tasks for other services, stopping")
                return [StopCommand(active_service.instance_id)]
            result = self._cooldown_respecting_delay(active_service)
            if len(result) > 0:
                args.log_handler.event("No tasks, cooldown time waited, stopping")
            return result

        if len(currently_at_active_service) >= 2:
            return []

        if len(next_for_active_service) == 0:
            return []

        next = next_for_active_service[0]
        args.log_handler.event(f'Assigning task {next.id}')
        return [AssignAction(next.id, active_service.instance_id, active_service.key)]








