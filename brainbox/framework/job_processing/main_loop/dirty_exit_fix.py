from ..core import ICoreAction, Job, Core

class DirtyExitFix(ICoreAction):
    def apply(self, core: Core):
        with core.new_session() as session:
            (
                session
                .query(Job)
                .filter(Job.finished_timestamp.is_(None) & Job.assigned_timestamp.is_not(None))
                .update({
                    Job.assigned_timestamp: None,
                    Job.accepted_timestamp: None,
                    Job.progress: None,
                    Job.log: None
                })
            )
            session.commit()