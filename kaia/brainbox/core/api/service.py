import copy
import time
from typing import *
from ..small_classes import BrainBoxJob, DeciderInstance, IDecider, LogItem, LogFactory, DeciderInstanceSpec
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from ....infra.comm import IMessenger
import traceback
from ..planers import IPlanner
from datetime import datetime
from yo_fluq import *
from pathlib import Path
import os
from dataclasses import dataclass

@dataclass
class FailedJobArgument:
    job: BrainBoxJob


class BrainBoxService:
    def __init__(self,
                 deciders: Dict[str, IDecider],
                 planer: IPlanner,
                 cache_folder: Path,
                 logger: Optional[Callable[[LogItem], Any]] = None
                 ):
        self.logger = LogFactory(logger)
        self.cache_folder = cache_folder
        self.planner = planer
        self.deciders = deciders

        self.decider_instances = {} #type: Dict[DeciderInstanceSpec, DeciderInstance]

        self.engine = None #type: Optional[Engine]
        self.messenger = None #type: Optional[IMessenger]


        self._exit_request = False
        self._terminated = False
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
        for instance in self.decider_instances.values():
            if instance.state.up:
                self.logger.decider(instance.state.spec).event('Cooldown request')
                instance.cool_down()
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
            self.iteration()
            time.sleep(0.01)

    def update_tasks(self):
        with Session(self.engine) as session:
            tasks = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.assigned.and_(~BrainBoxJob.finished))))
            for task in tasks:
                DeciderInstance.collect_status(task, self.messenger)
            session.commit()

    def iteration(self):
        self.remove_incorrect_tasks()
        self.update_tasks()
        self.assign_ready()


        with Session(self.engine) as session:
            non_finished_tasks = tuple(session.scalars(select(BrainBoxJob).where(~BrainBoxJob.finished)))
        states = tuple(instance.state for instance in self.decider_instances.values())
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
                    self.decider_instances[service] = DeciderInstance(service, self.deciders[service.decider_name], self.logger, self.cache_folder)
                    self.decider_instances[service].warm_up(self.messenger)
                except Exception as ex:
                    self.logger.decider(service).event("Warmup failed")
                    with Session(self.engine) as session:
                        tasks: Iterable[BrainBoxJob] = list(session.scalars(select(BrainBoxJob).where(~BrainBoxJob.finished)))
                        for task in tasks:
                            if task.get_decider_instance_spec() == service:
                                self.close_task(task, f'Decider {service} failed to warm up:\n{traceback.format_exc()}')
                        session.commit()


        if plan.assign_tasks is not None:
            for task_id in plan.assign_tasks:
                self.assign_task(task_id)


    def assign_task(self, task_id: str):
        with Session(self.engine) as session:
            task: BrainBoxJob = session.scalar(select(BrainBoxJob).where(BrainBoxJob.id == task_id))
            if task.finished:
                return
            arguments = task.arguments
            if task.dependencies is not None:
                requirements = list(task.dependencies.values())
                required_tasks = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id.in_(requirements))))
                for arg_name, id in task.dependencies.items():
                    dep: BrainBoxJob = Query.en(required_tasks).where(lambda z: z.id == id).single_or_default()
                    if dep is None:
                        self.close_task(task, f'Something is wrong: task was ready, but dependency {id} for argument {arg_name} was not found')
                        return
                    if not dep.success:
                        session.expunge(dep)
                        arguments[arg_name] = FailedJobArgument(dep)
                    else:
                        arguments[arg_name] = dep.result
            try:
                self.messenger.add(task, 'received', task.id)
                task.assigned = True
                task.assigned_timestamp = datetime.now()
                self.logger.task(task.id).event('Assigned')
            except:
                self.close_task(task)
                self.logger.task(task.id).event('Failed')
            finally:
                session.commit()


    def remove_incorrect_tasks(self):
        with Session(self.engine) as session:
            tasks = list(session.scalars(select(BrainBoxJob).where(~BrainBoxJob.finished)))
            for task in tasks:
                if task.decider not in self.deciders:
                    self.close_task(task, f'Decider {task.decider} is not found')
            session.commit()

    def close_task(self, task: BrainBoxJob, custom_message=None):
        self.logger.task(task.id).event('Failed at service level')
        if custom_message is None:
            custom_message = traceback.format_exc()
        task.finished = True
        task.success = False
        task.error = custom_message


    def assign_ready(self):
        with Session(self.engine) as session:
            not_ready_tasks = list(session.scalars(select(BrainBoxJob).where(~BrainBoxJob.ready).where(~BrainBoxJob.finished)))
            dependency_ids = Query.en(not_ready_tasks).where(lambda z: z.dependencies is not None).select_many(lambda z: z.dependencies.values()).to_list()
            dependency_tasks = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id.in_(dependency_ids))))
            id_to_task = {e.id: e for e in dependency_tasks}
            for task in not_ready_tasks:
                set_ready = True
                if task.dependencies is not None:
                    for id in task.dependencies.values():
                        if id not in id_to_task:
                            self.close_task(task, f"id {id} is required by this task but is absent")
                            set_ready = False
                            break

                        if not id_to_task[id].finished:
                            set_ready = False
                            break

                if set_ready:
                    task.ready = True
                    task.ready_timestamp = datetime.now()
                    self.logger.task(task.id).event('Ready')

            session.commit()












