import time
from ...architecture import Chara, logger
from brainbox import BrainBox
import json


def _print_log_remnants(old_log, new_log):
    if new_log is not None:
        if len(new_log) > len(old_log):
            for i in range(len(old_log), len(new_log)):
                logger.info(new_log[i])
                old_log.append(new_log[i])

def brainbox_training_pipeline(task: BrainBox.Task):
    @Chara.phase
    def task():
        return task

    @Chara.phase
    def task_id():
        id = Chara.Apis.brainbox_api.add(task)
        return id

    task_id: str = Chara.previous.result
    index = 0
    last_reported_progress = 0
    current_log = []
    while True:
        time.sleep(1)
        summary = Chara.Apis.brainbox_api.jobs.get_job_summary(task_id)
        if summary.finished_timestamp is not None:
            break
        new_progress = summary.progress
        if new_progress is not None and new_progress != last_reported_progress:
            last_reported_progress = new_progress
            logger.info(f'Reported progress: {int(last_reported_progress*100)}%')
        index += 1
        if index >= 10:
            index = 0
            job = Chara.Apis.brainbox_api.jobs.get_job(task_id)
            _print_log_remnants(current_log, job.log)

    job = Chara.Apis.brainbox_api.jobs.get_job(task_id)
    _print_log_remnants(current_log, job.log)

    if not job.success:
        raise ValueError(job.error)

    final_result = None
    text = Chara.Apis.brainbox_api.cache.read(job.result).decode('utf-8')
    for line in text.splitlines():
        data = json.loads(line)
        if data['result'] is not None:
            final_result = data['result']
            break

    return final_result





