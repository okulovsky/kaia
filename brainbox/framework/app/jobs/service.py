from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from brainbox.framework.job_processing.core.job import Job
from brainbox.framework.job_processing.main_loop import CancelAction, CommandQueue
from .dto import JobRecord
from .interface import IJobsService


class JobsService(IJobsService):
    def __init__(self, engine, command_queue: CommandQueue):
        self.engine = engine
        self.command_queue = command_queue

    def get_jobs(self, batch_id: str) -> list[JobRecord]:
        with Session(self.engine) as session:
            jobs: list[Job] = list(session.scalars(select(Job).where(Job.batch == batch_id)))

        records = []
        now = datetime.now()
        for j in jobs:
            in_queue = None
            if j.accepted_timestamp is not None:
                in_queue = (j.accepted_timestamp - j.received_timestamp).total_seconds()

            in_work = None
            if j.accepted_timestamp is not None:
                if j.finished_timestamp is not None:
                    in_work = (j.finished_timestamp - j.accepted_timestamp).total_seconds()
                else:
                    in_work = (now - j.accepted_timestamp).total_seconds()

            if j.finished_timestamp is not None and j.success:
                status = 'success'
            elif j.finished_timestamp is not None and not j.success:
                status = 'failure'
            elif j.accepted_timestamp is not None:
                status = 'in_work'
            else:
                status = 'waiting'

            if j.method:
                decider = f"{j.decider}:{j.method}"
            else:
                decider = j.decider

            records.append(JobRecord(
                id=j.id,
                batch=j.batch,
                decider=decider,
                received_timestamp=j.received_timestamp,
                accepted_timestamp=j.accepted_timestamp,
                finished_timestamp=j.finished_timestamp,
                in_queue=in_queue,
                in_work=in_work,
                status=status,
                progress=j.progress,
                error=j.error,
            ))

        records.sort(key=lambda r: r.received_timestamp, reverse=True)
        return records

    def cancel_job(self, job_id: str) -> None:
        self.command_queue.put_action(CancelAction(job_id, None))
