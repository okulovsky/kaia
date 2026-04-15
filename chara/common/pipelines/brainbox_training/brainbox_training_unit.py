import time
from dataclasses import dataclass

from ...cache import ICache, FileCache
from ...pipelines import logger, CharaApis
from pathlib import Path
from brainbox import BrainBox
from typing import Any, TextIO
import json

@dataclass
class BrainBoxTrainingCache(ICache):
    def __init__(self, work_folder: Path|None = None) -> None:
        super().__init__(work_folder)
        self.task = FileCache()
        self.task_id = FileCache[str](FileCache.Type.Text)

    def print_log_remnants(self, old_log, new_log):
        if new_log is not None:
            if len(new_log) > len(old_log):
                for i in range(len(old_log), len(new_log)):
                    logger.info(new_log[i])
                    old_log.append(new_log[i])

    def pipeline(self, task: BrainBox.Task):
        @logger.phase(self.task)
        def _():
            self.task.write(task)

        @logger.phase(self.task_id)
        def _():
            self.task_id.write(CharaApis.brainbox_api.add(task))

        task_id = self.task_id.read()
        index = 0
        last_reported_progress = 0
        current_log = []
        while True:
            time.sleep(1)
            summary = CharaApis.brainbox_api.summary([task_id])[0]
            if summary['finished_timestamp'] is not None:
                break
            new_progress = summary['progress']
            if new_progress is not None and new_progress != last_reported_progress:
                last_reported_progress = new_progress
                logger.info(f'Reported progress: {int(last_reported_progress*100)}%')
            index += 1
            if index >= 10:
                index = 0
                job = CharaApis.brainbox_api.job(task_id)
                self.print_log_remnants(current_log, job.log)

        job = CharaApis.brainbox_api.job(task_id)
        self.print_log_remnants(current_log, job.log)

        if not job.success:
            raise ValueError(job.error)

        final_result = None
        text = CharaApis.brainbox_api.open_file(job.result).string_content
        for line in text.splitlines():
            data = json.loads(line)
            if data['result'] is not None:
                final_result = data['result']
                break

        self.write_result(final_result)





