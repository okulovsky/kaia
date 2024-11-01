import copy
import time
from typing import *
from ..small_classes import BrainBoxJob, IDecider, LogItem, LogFactory, DeciderInstanceSpec
from .decider_instance import DeciderInstance
from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session
from ....infra.comm import IMessenger
import traceback
from ..planers import IPlanner, BrainBoxJobForPlanner
from datetime import datetime
from yo_fluq import *
from pathlib import Path
import os
from dataclasses import dataclass
import traceback

@dataclass
class FailedJobArgument:
    job: BrainBoxJob


class BrainBoxService:
    def __init__(self,
                 deciders: Dict[str, IDecider],
                 planer: IPlanner,
                 cache_folder: Path,
                 logger: Optional[Callable[[LogItem], Any]] = None,
                 main_iteration_sleep: float = 0.01,
                 raise_exceptions_in_main_cycle: bool = True
                 ):
        self.logger = LogFactory(logger)
        self.cache_folder = cache_folder
        self.planner = planer
        self.deciders = deciders

        self.decider_instances = {} #type: Dict[DeciderInstanceSpec, DeciderInstance]

        self.engine = None #type: Optional[Engine]
        self.messenger = None #type: Optional[IMessenger]

        self.non_finished_tasks_for_planner: List[BrainBoxJobForPlanner] = []
        self.main_iteration_sleep = main_iteration_sleep
        self.raise_exceptions_in_main_cycle = raise_exceptions_in_main_cycle


        self._exit_request = False
        self._terminated = False
        if self.cache_folder is not None:
            os.makedirs(self.cache_folder, exist_ok=True)

    def cancel(self, task_id):
        with Session(self.engine) as session:
            tasks = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id==task_id)))
            for task in tasks:
                task.finished = True
            session.commit()

    def terminate(self):
        self._terminated = False
        self._exit_request = True
        while not self._terminated:
            time.sleep(0.1)

    def terminate_internal(self):
        self.logger.service().event('Exiting')
        instances = tuple(instance.state for instance in self.decider_instances.values())
        cooldown_instances = self.planner.logout(instances)
        for instance in cooldown_instances:
            self.logger.decider(instance).event('Cooldown request')
            self.decider_instances[instance].cool_down()
        self.update_tasks()
        self._terminated = True


    def cycle(self,
              engine: Engine,
              messenger: IMessenger
              ):
        self.engine = engine
        self.messenger = messenger
        self.logger.service().event("Starting")
        while True:
            if self._exit_request:
                self.terminate_internal()
                return
            try:
                self.iteration()
            except:
                if self.raise_exceptions_in_main_cycle:
                    raise
                else:
                    print(traceback.format_exc())
            time.sleep(self.main_iteration_sleep)


    def iteration(self):
        self.remove_incorrect_tasks()
        self.update_tasks()
        self.assign_ready()
        self.run_planer()


    def update_tasks(self):
        with Session(self.engine) as session:
            tasks = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.assigned.and_(~BrainBoxJob.finished))))
            for task in tasks:
                DeciderInstance.collect_status(task, self.messenger)
            session.commit()


    def get_non_finished_tasks(self):
        with Session(self.engine) as session:
            current_ids = [z.id for z in self.non_finished_tasks_for_planner]
            finished_ids = list(session.scalars(
                select(BrainBoxJob.id)
                .where(BrainBoxJob.finished & BrainBoxJob.id.in_(current_ids))
            ))
            new_records = list(session.execute(
                select(
                    BrainBoxJob.id,
                    BrainBoxJob.decider,
                    BrainBoxJob.decider_parameters,
                    BrainBoxJob.received_timestamp,
                    BrainBoxJob.assigned,
                    BrainBoxJob.ordering_token
                )
                .where(
                    ~BrainBoxJob.finished &
                    BrainBoxJob.ready &
                    BrainBoxJob.id.notin_(current_ids)

                )
            ))
            self.non_finished_tasks_for_planner = [z for z in self.non_finished_tasks_for_planner if z.id not in finished_ids]
            self.non_finished_tasks_for_planner.extend([BrainBoxJobForPlanner(*rec) for rec in new_records])
            return self.non_finished_tasks_for_planner


    def _get_states_for_planner(self):
        states = tuple(instance.state for instance in self.decider_instances.values())
        return states

    def run_planer(self):
        non_finished_tasks = self.get_non_finished_tasks()
        states = self._get_states_for_planner()

        plan = self.planner.plan(non_finished_tasks, states)

        if plan.cool_down is not None:
            for service in plan.cool_down:
                self.logger.decider(service).event('Cooldown request')
                self.decider_instances[service].cool_down()
                del self.decider_instances[service]


        if plan.warm_up is not None:
            for service in plan.warm_up:
                try:
                    self.logger.decider(service).event('Warmup request')
                    if service.decider_name not in self.deciders:
                        raise ValueError(f'Decider {service.decider_name} is not found, available {list(self.deciders)}')
                    shallow_warmup = self.planner.shallow_warmup_only(service, self._get_states_for_planner())
                    self.decider_instances[service] = DeciderInstance(service, self.deciders[service.decider_name], self.logger, self.cache_folder)
                    self.decider_instances[service].warm_up(self.messenger, shallow_warmup)
                except Exception as ex:
                    self.logger.decider(service).event("Warmup failed")
                    with Session(self.engine) as session:
                        tasks: Iterable[BrainBoxJob] = list(session.scalars(
                            select(BrainBoxJob)
                            .where(
                                ~BrainBoxJob.finished &
                                (BrainBoxJob.decider==service.decider_name) &
                                (BrainBoxJob.decider_parameters == service.parameters)
                            )
                        ))
                        for task in tasks:
                            if task.get_decider_instance_spec() == service:
                                self.close_task(task, f'Decider {service} failed to warm up:\n{traceback.format_exc()}')
                        session.commit()


        if plan.assign_tasks is not None:
            for task_id in plan.assign_tasks:
                self.assign_task(task_id)


    def assign_task(self, task_id: str):
        with Session(self.engine) as session:
            task = self.get_task_by_id(session, task_id)
            if task.finished:
                return
            arguments = task.arguments
            if task.dependencies is not None:
                requirements = list(task.dependencies.values())
                requirement_to_result = {}
                for element in session.scalars(select(BrainBoxJob).where(BrainBoxJob.id.in_(requirements))):
                    if element.success:
                        requirement_to_result[element.id] = element.result
                    else:
                        session.expunge(element)
                        requirement_to_result[element.id] = FailedJobArgument(element)

                for arg_name, id in task.dependencies.items():
                    if id not in requirement_to_result:
                        self.close_task(task, f'Something is wrong: task was ready, but dependency {id} for argument {arg_name} was not found')
                        return
                    if isinstance(arg_name, str) and len(arg_name)>0 and arg_name[0]!='*':
                        arguments[arg_name] = requirement_to_result[id]

            try:
                self.messenger.add(task, 'received', task.id)
                task.assigned = True
                task_for_planner = Query.en(self.non_finished_tasks_for_planner).where(lambda z: z.id == task_id).single()
                task_for_planner.assigned = True
                task.assigned_timestamp = datetime.now()
                self.logger.task(task.id).event('Assigned')
            except:
                self.close_task(task)
                self.logger.task(task.id).event('Failed')
            finally:
                session.commit()


    def remove_incorrect_tasks(self):
        with Session(self.engine) as session:
            deciders = list(self.deciders)
            tasks = list(session.execute(
                select(BrainBoxJob.id, BrainBoxJob.decider)
                .where(
                    ~BrainBoxJob.finished &
                    ~BrainBoxJob.decider.in_(deciders)
            )))
            for task in tasks:
                self.close_task(self.get_task_by_id(session, task.id), f'Decider {task.decider} is not found. Available are: {deciders}')
            session.commit()

    def get_task_by_id(self, session: Session, id: str):
        return session.scalar(select(BrainBoxJob).where(BrainBoxJob.id == id))


    def close_task(self, task: BrainBoxJob, custom_message=None):
        self.logger.task(task.id).event('Failed at service level')
        if custom_message is None:
            custom_message = traceback.format_exc()
        task.finished = True
        task.success = False
        task.error = custom_message


    def assign_ready(self):
        self.assign_ready_to_independent_tasks()
        self.assign_ready_to_dependent_tasks()

    def assign_ready_to_independent_tasks(self):
        with Session(self.engine) as session:
            (
                session
                .query(BrainBoxJob)
                .filter(
                    ~BrainBoxJob.finished & ~BrainBoxJob.ready & ~BrainBoxJob.has_dependencies
                )
                .update({BrainBoxJob.ready: True, BrainBoxJob.ready_timestamp:datetime.now()})
            )
            session.commit()


    def assign_ready_to_dependent_tasks(self):
        with Session(self.engine) as session:
            dependent_tasks = list(session.execute(
                select(BrainBoxJob.id, BrainBoxJob.dependencies)
                .where(~BrainBoxJob.finished & ~BrainBoxJob.ready & BrainBoxJob.has_dependencies)
            ))

            dependency_ids = list(set(id for dependent in dependent_tasks for id in dependent.dependencies.values()))

            dependency_status = list(session.execute(
                select(BrainBoxJob.id, BrainBoxJob.finished)
                .where(BrainBoxJob.id.in_(dependency_ids))
            ))
            id_to_finished = {status.id: status.finished for status in dependency_status}

            for task in dependent_tasks:
                set_ready = True
                for id in task.dependencies.values():
                    if id not in id_to_finished:
                        self.close_task(self.get_task_by_id(session, task.id), f"id {id} is required by this task but is absent")
                    elif not id_to_finished[id]:
                        set_ready = False
                        break
                if set_ready:
                    task_obj = self.get_task_by_id(session, task.id)
                    task_obj.ready = True
                    task_obj.ready_timestamp = datetime.now()
                    self.logger.task(task_obj.id).event('Ready')

            session.commit()












