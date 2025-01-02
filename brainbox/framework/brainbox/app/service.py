from ...common.marshalling import endpoint
from .interface import IBrainboxService
from ...controllers import ControllerRegistry
from ...job_processing import IPlanner, MainLoop, Core, Job, SimplePlanner, OperatorLogItem, FailedJobArgument
from dataclasses import dataclass, field
from pathlib import Path
from ...common import Loc, Locator
from sqlalchemy import create_engine, select, Engine
from sqlalchemy.orm import Session
from threading import Thread
from datetime import datetime, timedelta
from ...job_processing.core.job import BrainBoxBase
import time

@dataclass
class BrainBoxServiceSettings:
    registry: ControllerRegistry
    planner: IPlanner = field(default_factory=SimplePlanner)
    port: int = 18090
    debug_output: bool = False
    locator: Locator = Loc
    stop_controllers_at_termination: bool = True




class BrainBoxService(IBrainboxService):
    def __init__(self, settings: BrainBoxServiceSettings):
        self.settings = settings


    def run(self):
        self.engine = create_engine('sqlite:///'+str(self.settings.locator.db_path))
        BrainBoxBase.metadata.create_all(self.engine)
        core = Core(self.engine, self.settings.registry, self.settings.locator, self.settings.debug_output)
        self.loop = MainLoop(core, self.settings.planner, self.settings.stop_controllers_at_termination)
        self.loop_thread = Thread(target=self.loop.run)
        self.loop_thread.start()

    @endpoint(url='/jobs/add', method='POST')
    def base_add(self, jobs:list[dict]):
        now = datetime.now()
        with Session(self.engine) as session:
            for i, job_dict in enumerate(jobs):
                job = Job(**job_dict)
                job = job.set_defaults(now + timedelta(microseconds=i))
                session.add(job)
            session.commit()

    @endpoint(url='/jobs/join', method='GET')
    def base_join(self,
                  ids: list[str],
                  time_limit_in_secods: int|None = None,
                  allow_failures: bool = False
                  ) -> list:
        begin = datetime.now()
        while True:
            with Session(self.engine) as session:
                jobs: list[Job] = list(session.scalars(select(Job).where(Job.id.in_(ids))))
            if len(jobs) != len(ids):
                missing = list(set(ids) - set(j.id for j in jobs))
                raise ValueError(f'Join_execute is missing jobs for ids {missing}')
            id_to_job = {}
            for job in jobs:
                if not job.finished:
                    break
                if not job.success:
                    if allow_failures:
                        id_to_job[job.id] = FailedJobArgument(job)
                    else:
                        stars='*~'*30
                        raise ValueError(f"{job.decider}/{job.decider_parameter}:{job.method} threw an error:\n{stars}\n{job.error}\n{stars}")
                else:
                    id_to_job[job.id] = job
            if len(id_to_job) == len(ids):
                result = []
                for id in ids:
                    if isinstance(id_to_job[id], FailedJobArgument):
                        result.append(id_to_job[id])
                    else:
                        result.append(id_to_job[id].result)
                return result
            if time_limit_in_secods is not None:
                delta = datetime.now() - begin
                if delta.total_seconds() > time_limit_in_secods:
                    raise ValueError(f"Could not wait for join in {time_limit_in_secods} seconds")
            time.sleep(0.1)

    @endpoint(url='/jobs/result', method='GET')
    def result(self, id: str):
        with Session(self.engine) as session:
            result = list(session.scalars(select(Job.result).where(Job.finished.and_(Job.id == id))))
            if len(result)==0:
                return None
            return result[0]


    @endpoint(url='/jobs/summary', method='GET')
    def summary(self, ids: list[str]|None = None, batch_id: str|None = None) -> list[dict]:
        query = select(
            Job.id, Job.decider, Job.decider_parameter, Job.method, Job.batch, Job.info, Job.received_timestamp,
            Job.ready, Job.ready_timestamp, Job.assigned, Job.assigned_timestamp, Job.accepted,
            Job.accepted_timestamp, Job.finished, Job.finished_timestamp, Job.success, Job.error,
        )
        if ids is not None:
            query = query.where(Job.id.in_(ids))
        if batch_id is not None:
            query = query.where(Job.batch==batch_id)
        with Session(self.engine) as session:
            rows = list(dict(r._mapping) for r in session.execute(query))
        return rows

    @endpoint(url='/jobs/cancel', method='POST')
    def cancel(self, job_id: str|None = None, batch_id: str|None = None):
        self.loop.cancel(job_id, batch_id)

    @endpoint(url='/jobs/job', method='GET')
    def job(self, id: str):
        with Session(self.engine) as session:
            result = list(session.scalars(select(Job).where(Job.finished.and_(Job.id == id))))
        if len(result) == 0:
            raise ValueError(f"Can't find a job with the id {id}")
        return result[0]

    @endpoint(url='/jobs/operator_log', method='GET')
    def get_operator_log(self, entries_count: int = 100) -> list[OperatorLogItem]:
        return self.loop.core.operator_log.log_items[-entries_count:]

    @endpoint(url='/shutdown', method='POST')
    def shutdown(self):
        self.loop.terminate()
        self.loop_thread.join()
        self.engine.dispose()

    @property
    def cache_folder(self) -> Path:
        return self.settings.locator.cache_folder

