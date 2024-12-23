from ..core import ICoreAction, Core, Job
from sqlalchemy.orm import Session
from sqlalchemy import select


class RemoveIncorrectJobsAction(ICoreAction):
    def apply(self, core: Core):
        with core.new_session() as session:
            deciders = core.registry.get_deciders_names()
            jobs = list(session.scalars(select(Job).where(~Job.finished & ~Job.decider.in_(deciders))))
            for job in jobs:
                core.close_job(session, job, f'Decider {job.decider} is not found. Available are: {deciders}')
            session.commit()