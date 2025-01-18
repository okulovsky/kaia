from ..core import Core, ICoreAction, JobForPlanner, Job
from sqlalchemy import select
from datetime import datetime



class TaskForPlannerSyncWithLastUpdated(ICoreAction):
    def __init__(self):
        self.last_time_full_update: datetime|None = None
        self.last_time_small_update_in_db_clock: datetime|None = None


    def should_do_full_update(self, core):
        if self.last_time_full_update is None:
            return True
        if self.last_time_small_update_in_db_clock is None:
            return True
        if core.jobs_for_planner is None:
            return True
        if (datetime.now() - self.last_time_full_update).total_seconds() > 5:
            return True
        return False

    def apply(self, core: Core):
        with core.new_session() as session:
            if self.should_do_full_update(core):
                self.last_time_full_update = datetime.now()
                core.jobs_for_planner = self._get_tasks(session)
                return

            updates = self._get_tasks(session, self.last_time_small_update_in_db_clock)
            changed = set(u.id for u in updates)
            not_changed = tuple(
                job
                for job in core.jobs_for_planner
                if job.id not in changed
            )
            core.jobs_for_planner = not_changed + updates


    def _get_tasks(self, session, from_timestamp: datetime|None = None):
        condition = ~Job.finished & Job.ready
        if from_timestamp is not None:
            condition &= Job.last_update_timestamp>=from_timestamp
        new_records = list(session.execute(
            select(
                Job.id,
                Job.decider,
                Job.decider_parameter,
                Job.received_timestamp,
                Job.assigned,
                Job.ordering_token,
                Job.last_update_timestamp
            )
            .where(condition)
        ))
        result = []
        for rec in new_records:
            if self.last_time_small_update_in_db_clock is None or rec[-1]>self.last_time_small_update_in_db_clock:
                self.last_time_small_update_in_db_clock = rec[-1]
            result.append(JobForPlanner(*rec[:-1]))
        return tuple(result)