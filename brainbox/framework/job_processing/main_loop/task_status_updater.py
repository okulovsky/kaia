from ..core import Core, ICoreAction, OperatorMessage, Job
from pprint import pprint

class TasksStatusUpdater(ICoreAction):
    def apply(self, core: Core):
        updates = []
        for operator_state in core.operator_states.values():
            while not operator_state.results_queue.empty():
                updates.append(operator_state.results_queue.get())

        if len(updates) == 0:
            return

        id_to_job = {}
        with core.new_session() as session:
            for update in updates:
                if update.id not in id_to_job:
                    id_to_job[update.id] = core.get_job_by_id(session, update.id)
                self._apply_update(core, update, id_to_job[update.id])
            session.commit()



    def _apply_update(self, core, update: OperatorMessage, job: Job):
        if update.type == OperatorMessage.Type.accepted:
            job.accepted_timestamp = update.timestamp

        elif update.type == OperatorMessage.Type.error:
            job.error = update.payload
            job.success = False
            job.finished_timestamp = update.timestamp

        elif update.type == OperatorMessage.Type.result:
            job.result = update.payload
            job.success = True
            job.finished_timestamp = update.timestamp

        elif update.type == OperatorMessage.Type.report_progress:
            job.progress = update.payload

        elif update.type == OperatorMessage.Type.log:
            existing = list(job.log) if job.log is not None else []
            existing.append(update.payload)
            job.log = existing

        elif update.type == OperatorMessage.Type.responding:
            job.responding_timestamp = update.timestamp
            job.result = update.payload

        else:
            raise ValueError(f"Unknown update type {update.type}")



