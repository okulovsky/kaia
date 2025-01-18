from ..core import ICoreAction, Job, Core

class DirtyExitFix(ICoreAction):
    def apply(self, core: Core):
        with core.new_session() as session:
            (
                session
                .query(Job)
                .filter(~Job.finished & Job.assigned)
                .update({
                    Job.assigned: False,
                    Job.assigned_timestamp: None,
                    Job.accepted: False,
                    Job.accepted_timestamp: None,
                    Job.progress: None,
                    Job.log: None
                })
            )
            session.commit()