from typing import *
from ....framework import BrainBoxTask, BrainBoxTaskPack, IBrainBoxTask
from pathlib import Path
import dataclasses



class TaskBuilder:
    @dataclasses.dataclass
    class Record:
        task: IBrainBoxTask
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

    def append(self, task: IBrainBoxTask, tags: None | dict[str, Any]):
        if self._can_add():
            self.records.append(TaskBuilder.Record(task, tags))
        return task

    def to_collector_pack(self, method: str):
        dependencies = {}
        tags = {}
        tasks = []

        for record in self.records:
            tasks.append(record.task)
            if record.tags is not None:
                tags[record.task.get_resulting_id()] = record.tags
                dependencies[record.task.get_resulting_id()] = record.task.get_resulting_id()

        resulting_task = BrainBoxTask(
            decider='Collector',
            decider_method=method,
            dependencies=dependencies,
            arguments=dict(tags=tags)
        )

        for task in tasks:
            task.batch = resulting_task.id
        resulting_task.batch = resulting_task.id

        return BrainBoxTaskPack(
            resulting_task,
            tuple(tasks),
            uploads=self.uploads
        )

