import copy
import dataclasses
import json
from typing import *

import pandas as pd

from kaia.brainbox.core import IDecider, FailedJobArgument, File, BrainBoxTask, BrainBoxTaskPack
from kaia.brainbox.core.small_classes.task_builder import BrainBoxTaskBuilderResult
from kaia.brainbox.media_library import MediaLibrary
from kaia.infra import FileIO
from uuid import uuid4
from datetime import datetime


class Collector(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def to_media_library(self, tags: Dict[str, Dict], **kwargs):
        errors = []
        records = []
        for id, tags in tags.items():
            if id not in kwargs:
                errors.append(f'Id {id} not in the list of jobs')
                continue
            result = kwargs[id]
            if isinstance(result,FailedJobArgument):
                errors.append(f'Task {id} failed: {result.job.error}')
                continue
            if isinstance(result, str):
                result = [result]
            elif isinstance(result, File):
                result = [result]
            else:
                try:
                    result = list(result)
                except:
                    raise ValueError("To be included in the MediaLibrary, the output of the job must be File, str or list of those")
            for file_index, file in enumerate(result):
                tags_copy = copy.copy(tags)

                inline_kwarg = {}
                if not isinstance(file, File):
                    inline_kwarg['inline_content'] = file

                record = MediaLibrary.Record(
                    filename = file.name,
                    holder_location = self.file_cache,
                    timestamp = datetime.now(),
                    job_id = id,
                    tags = tags_copy,
                    **inline_kwarg
                )
                record.tags['option_index'] = file_index
                records.append(record)
        library = MediaLibrary(tuple(records), tuple(errors))
        fname = f'{self.current_job_id}.output.zip'
        library.save(self.file_cache/fname)
        return fname


    def to_array(self, tags: dict[str,dict], **kwargs):
        final_result = []
        for key, value in tags.items():
            item_result = dict(tags=value)
            if key not in kwargs:
                raise ValueError(f"Id {key} in tags, but not in kwargs")
            job_result = kwargs[key]
            if isinstance(job_result, FailedJobArgument):
                item_result['result'] = None
                item_result['error'] = job_result.job.error
            else:
                item_result['result'] = job_result
                item_result['error'] = None
            final_result.append(item_result)
        return final_result

    def to_dict(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, FailedJobArgument):
                raise ValueError(f"Dependency failed on argument {key}:\n{value.job.error}")
        return kwargs



    class PackBuilder:
        @dataclasses.dataclass
        class Record:
            task: BrainBoxTask
            tags: dict[str, Any]


        def __init__(self, records: Optional[Iterable['Collector.PackBuilder.Record']] = None):
            self.records = [] if records is None else list(records)

        def append(self, task: BrainBoxTask|BrainBoxTaskBuilderResult, tags: dict[str, Any]):
            if isinstance(task, BrainBoxTaskBuilderResult):
                task = task.to_task()
            self.records.append(Collector.PackBuilder.Record(task, tags))


        def to_collector_pack(self, method: str):
            dependencies = {}
            tags = {}
            tasks = []

            for record in self.records:
                tasks.append(record.task)
                tags[record.task.id] =record.tags
                dependencies[record.task.id] = record.task.id

            return BrainBoxTaskPack(
                BrainBoxTask(
                    decider='Collector',
                    decider_method=method,
                    dependencies=dependencies,
                    arguments=dict(tags=tags)
                ),
                tuple(tasks),
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
        