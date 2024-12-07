from typing import *
from ...core import BrainBoxTask, BrainBoxTaskPack
from ...core.small_classes.task_builder import BrainBoxTaskBuilderResult
from pathlib import Path
import dataclasses
import copy
import pandas as pd


class CollectorTaskBuilder:
    @dataclasses.dataclass
    class Record:
        task: BrainBoxTask
        tags: None | dict[str, Any]

    def __init__(self,
                 records: Optional[Iterable['CollectorTaskBuilder.Record']] = None,
                 limit_records_for_test_purposes_at: None | int = None
                 ):
        self.records = [] if records is None else list(records)
        self.limit_records_for_test_purposes_at = limit_records_for_test_purposes_at
        self.uploads: dict[str, Path] = {}

    def _can_add(self):
        if self.limit_records_for_test_purposes_at is None:
            return True
        return len(self.records) < self.limit_records_for_test_purposes_at

    def append(self, task: BrainBoxTask | BrainBoxTaskBuilderResult, tags: None | dict[str, Any]):
        if isinstance(task, BrainBoxTaskBuilderResult):
            task = task.to_task()
        if self._can_add():
            self.records.append(CollectorTaskBuilder.Record(task, tags))
        return task

    def to_collector_pack(self, method: str):
        dependencies = {}
        tags = {}
        tasks = []

        for record in self.records:
            tasks.append(record.task)
            if record.tags is not None:
                tags[record.task.id] = record.tags
                dependencies[record.task.id] = record.task.id

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

    def to_debug_array(self) -> list[dict]:
        result = []
        for record in self.records:
            args = copy.copy(record.task.arguments)
            for k, v in record.tags.items():
                args[k] = v
            result.append(args)
        return result

    def to_debug_df(self):
        return pd.DataFrame(self.to_debug_array())