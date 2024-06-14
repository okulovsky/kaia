import copy
import json
from typing import *
from ...core import IDecider, FailedJobArgument
from ...media_library import MediaLibrary
from ....infra import FileIO
from uuid import uuid4
from datetime import datetime


class Collector(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, tags: Dict[str, Dict], **kwargs):
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
            for file_index, file in enumerate(result):
                tags_copy = copy.copy(tags)
                record = MediaLibrary.Record(
                    filename = file,
                    holder_location = self.file_cache,
                    timestamp = datetime.now(),
                    job_id = id,
                    tags = tags_copy
                )
                record.tags['option_index'] = file_index
                records.append(record)
        library = MediaLibrary(tuple(records), tuple(errors))
        fname = f'{uuid4()}.zip'
        library.save(self.file_cache/fname)
        return fname


    def collect_outputs(self, tags: Dict[str, Dict], **kwargs):
        errors = []
        records = []
        for id, tags in tags.items():
            if id not in kwargs:
                errors.append(f'Id {id} not in the list of jobs')
                continue
            result = kwargs[id]
            if isinstance(result, FailedJobArgument):
                errors.append(f'Task {id} failed: {result.job.error}')
                continue
            records.append(dict(
                job_id = id,
                tags = tags,
                timestamp = datetime.now(),
                result = result
            ))

        fname = f'{uuid4()}.pkl'
        FileIO.write_pickle(
            dict(records=records, errors=errors),
            self.file_cache/fname
        )
        return fname
