import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from brainbox.framework.job_processing.core.job import Job
from brainbox.framework.job_processing.main_loop.command_queue import CommandQueue
from brainbox.framework.job_processing.main_loop.new_tasks_action import NewTasksAction
from brainbox.framework.task import JobDescription
from foundation_kaia.marshalling import JSON
from .dto import JobSummary
from .interface import ITasksService


class TasksService(ITasksService):
    def __init__(self, engine, command_queue: CommandQueue):
        self.engine = engine
        self.command_queue = command_queue

    def base_add(self, jobs: list[JobDescription]) -> list[str]:
        now = datetime.now()
        ids = []
        with Session(self.engine) as session:
            for i, job_description in enumerate(jobs):
                if job_description.id is None:
                    job_description.id = str(uuid.uuid4())
                job = job_description.to_job()
                job.received_timestamp = now + timedelta(microseconds=i)
                ids.append(job.id)
                session.add(job)
            session.commit()
        self.command_queue.put_action(NewTasksAction())
        return ids

    def base_join(self, ids: list[str], timeout_in_seconds: float | None = None, ignore_errors: bool | None = None) -> list[Any]:
        deadline = None if timeout_in_seconds is None else time.time() + timeout_in_seconds
        while True:
            with Session(self.engine) as session:
                jobs: list[Job] = list(session.scalars(select(Job).where(Job.id.in_(ids))))
            if len(jobs) != len(ids):
                missing = list(set(ids) - set(j.id for j in jobs))
                raise ValueError(f'Join is missing jobs for ids {missing}')
            id_to_result = {}
            all_finished = True
            for job in jobs:
                if not job.finished:
                    all_finished = False
                    break
                if not job.success:
                    if not ignore_errors:
                        stars = '*~' * 30
                        raise ValueError(
                            f"{job.decider}/{job.parameter}:{job.method} threw an error:\n{stars}\n{job.error}\n{stars}"
                        )
                id_to_result[job.id] = job.result
            if all_finished:
                return [id_to_result[id] for id in ids]
            if deadline is not None and time.time() >= deadline:
                raise TimeoutError(f'Timed out waiting for jobs: {ids}')
            time.sleep(0.01)

    def get_job(self, id: str) -> Job:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return job

    def get_result(self, id: str) -> Any:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return job.result

    def get_job_summary(self, id: str) -> JobSummary:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return JobSummary.from_job(job)

    def get_summaries(self) -> list[JobSummary]:
        with Session(self.engine) as session:
            jobs = list(session.scalars(select(Job)))
        return [JobSummary.from_job(job) for job in jobs]

    def get_info(self, id: str) -> JSON:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return job.info

    def get_error(self, id: str) -> str:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return job.error

    def get_log(self, id: str) -> list[str]:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).where(Job.id == id))
        if job is None:
            raise ValueError(f"Can't find a job with id {id}")
        return job.log
