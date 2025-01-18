from ..core import Core, ICoreAction, JobForPlanner, Job
from sqlalchemy import select
from datetime import datetime



class TaskForPlannerSyncWithTracking(ICoreAction):
    def __init__(self):
        self.last_time_full_update: datetime|None = None


    def should_do_full_update(self, core):
        if self.last_time_full_update is None:
            return True
        if core.jobs_for_planner is None:
            return True
        if (datetime.now() - self.last_time_full_update).total_seconds() > 5:
            return True
        if len(core.jobs_for_planner) < 100: #This is the optimization for really big loads. Doesn't make sense to do it for smaller
            return True
        return False

    def apply(self, core: Core):
        with core.new_session() as session:
            if self.should_do_full_update(core):
                self.last_time_full_update = datetime.now()
                core.jobs_for_planner = self._get_tasks(session)
                return

            changed = set(core.new_session.changes.all)
            not_changed = tuple(
                job
                for job in core.jobs_for_planner
                if job.id not in changed
            )
            core.jobs_for_planner = not_changed + self._get_tasks(session, set(j.id for j in not_changed))
            core.new_session.reset()



    def _get_tasks(self, session, skip_for_ids: None|set = None):
        condition = ~Job.finished & Job.ready
        if skip_for_ids is not None:
            condition &= Job.id.notin_(skip_for_ids)
        new_records = list(session.execute(
            select(
                Job.id,
                Job.decider,
                Job.decider_parameter,
                Job.received_timestamp,
                Job.assigned,
                Job.ordering_token
            )
            .where(condition)
        ))
        return tuple(JobForPlanner(*rec) for rec in new_records)
