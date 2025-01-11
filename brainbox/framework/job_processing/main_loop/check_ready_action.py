from ..core import ICoreAction, Job, Core
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime


class CheckReadyAction(ICoreAction):
    def apply(self, core: Core):
        self.assign_ready_to_independent_tasks(core)
        self.assign_ready_to_dependent_tasks(core)

    def assign_ready_to_independent_tasks(self, core: Core):
        with core.new_session() as session:
            (
                session
                .query(Job)
                .filter(
                    ~Job.finished & ~Job.ready & ~Job.has_dependencies
                )
                .update({Job.ready: True, Job.ready_timestamp:datetime.now()})
            )
            session.commit()


    def assign_ready_to_dependent_tasks(self, core: Core):
        with core.new_session() as session:
            dependent_tasks = list(session.execute(
                select(Job.id, Job.dependencies)
                .where(~Job.finished & ~Job.ready & Job.has_dependencies)
            ))

            dependency_ids = list(set(id for dependent in dependent_tasks for id in dependent.dependencies.values()))

            dependency_status = list(session.execute(
                select(Job.id, Job.finished)
                .where(Job.id.in_(dependency_ids))
            ))
            id_to_finished = {status.id: status.finished for status in dependency_status}

            for task in dependent_tasks:
                set_ready = True
                for id in task.dependencies.values():
                    if id not in id_to_finished:
                        core.close_job(
                            session,
                            core.get_job_by_id(session, task.id),
                            f"id {id} is required by this task but is absent"
                        )
                    elif not id_to_finished[id]:
                        set_ready = False
                        break
                if set_ready:
                    task_obj = core.get_job_by_id(session, task.id)
                    task_obj.ready = True
                    task_obj.ready_timestamp = datetime.now()
                    core.operator_log.task(task_obj.id).event('Ready')


            session.commit()