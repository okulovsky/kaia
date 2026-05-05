import uuid
from typing import *
from ....framework import JobRequest, IJobRequestFactory, JobDescription
from pathlib import Path
import dataclasses



class TaskBuilder:
    @dataclasses.dataclass
    class Record:
        job_request: JobRequest
        tags: None | dict[str, Any]

    def __init__(self,
                 records: Optional[Iterable['TaskBuilder.Record']] = None,
                 limit_records_for_test_purposes_at: None | int = None
                 ):
        self.records = [] if records is None else list(records)
        self.limit_records_for_test_purposes_at = limit_records_for_test_purposes_at
        self.uploads: dict[str, Path] = {}

    def _can_add(self):
        if self.limit_records_for_test_purposes_at is None:
            return True
        return len(self.records) < self.limit_records_for_test_purposes_at

    def append(self, task: IJobRequestFactory, tags: None | dict[str, Any] = None):
        if self._can_add():
            self.records.append(TaskBuilder.Record(task.to_job_request(), tags))
        return task

    def to_collector_pack(self, method: str, **kwargs):
        dependencies = {}
        tags = {}
        descriptions = []
        for record in self.records:
            if record.tags is not None:
                tags[record.job_request.main_id] = record.tags
                dependencies[record.job_request.main_id] = record.job_request.main_id
            descriptions.extend(record.job_request.jobs)

        collector_description = JobDescription(
            decider='Collector',
            arguments=dict(tags=tags),
            id = str(uuid.uuid4()),
            dependencies=dependencies,
            method=method
        )
        jobs = (collector_description,)+tuple(descriptions)

        result = JobRequest(
            jobs
        )


        return result



