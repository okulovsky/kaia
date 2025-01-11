from dataclasses import dataclass
from ..core import DeciderInstanceKey, Core, Job
from .planner_action import IPlannerAction
from sqlalchemy import select
from datetime import datetime
import copy

@dataclass
class FailedJobArgument:
    job: Job

@dataclass
class AssignAction(IPlannerAction):
    job_id: str
    instance_id: str
    key: DeciderInstanceKey

    def apply(self, core: Core):
        with core.new_session() as session:
            job = core.get_job_by_id(session, self.job_id)
            if job.finished:
                return
            arguments = job.arguments
            if job.dependencies is not None:
                requirements = list(job.dependencies.values())
                requirement_to_result = {}
                for element in session.scalars(select(Job).where(Job.id.in_(requirements))):
                    if element.success:
                        requirement_to_result[element.id] = element.result
                    else:
                        session.expunge(element)
                        requirement_to_result[element.id] = FailedJobArgument(element)

                for arg_name, id in job.dependencies.items():
                    if id not in requirement_to_result:
                        core.close_job(
                            session,
                            job,
                            f'Something is wrong: task was ready, but dependency {id} for argument {arg_name} was not found'
                        )
                        return
                    if isinstance(arg_name, str) and len(arg_name) > 0 and arg_name[0] != '*':
                        arguments[arg_name] = requirement_to_result[id]

            try:
                job_clone = copy.copy(job)
                core.operator_states[self.instance_id].jobs_queue.put(job_clone)
                job.assigned = True
                job.assigned_timestamp = datetime.now()
                core.operator_log.task(self.job_id).event('Assigned')
            except:
                core.close_job(session, job, "Assignment failed")

            finally:
                session.commit()