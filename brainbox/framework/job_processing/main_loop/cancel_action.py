from ..core import ICoreAction, Core, Job
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CancelAction(ICoreAction):
    cancel_job_id: str|None
    cancel_batch_id: str|None

    def apply(self, core: Core):
        condition = ~Job.finished
        if self.cancel_job_id is not None:
            condition &= Job.id == self.cancel_job_id
        if self.cancel_batch_id is not None:
            condition &= Job.batch == self.cancel_batch_id
        with core.new_session() as session:
            jobs = list(session.scalars(select(Job).where(condition)))
            for job in jobs:
                core.close_job(session, job.id, 'Cancelled')
            session.commit()