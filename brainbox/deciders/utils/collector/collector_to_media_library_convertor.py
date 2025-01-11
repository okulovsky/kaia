import uuid
from typing import *
from ....framework import FailedJobArgument, MediaLibrary
from datetime import datetime
from pathlib import Path
import copy

class CollectorToMediaLibraryConvertor:
    def __init__(self, current_job_id: str, cache_folder: Path, tags: dict[str, dict], results: dict):
        self.current_job_id = current_job_id
        self.cache_folder = cache_folder
        self.tags = tags
        self.results = results
        self.errors = []
        self.records = []

    def _parse_result(self, id: str) -> list[str]|None:
        result = self.results[id]
        if isinstance(result, FailedJobArgument):
            self.errors.append(f'Task {id} failed: {result.job.error}')
            return None
        if isinstance(result, str):
            return [result]
        else:
            try:
                return(list(result))
            except:
                raise ValueError(
                    f"To be included in the MediaLibrary, the output of the job must be str or list of strings, but was {result}")


    def _process_one_record(self, id: str, index: int, record: str):
        tags_copy = copy.copy(self.tags[id])

        inline_kwarg = {}

        if (self.cache_folder/record).is_file():
            fname = record
        else:
            fname = str(uuid.uuid4())
            inline_kwarg['inline_content'] = record

        record = MediaLibrary.Record(
            filename=fname,
            holder_location=self.cache_folder,
            timestamp=datetime.now(),
            job_id=id,
            tags=tags_copy,
            **inline_kwarg
        )
        record.tags['option_index'] = index
        self.records.append(record)

    def convert(self):
        for id, tags in self.tags.items():
            if id not in self.results:
                self.errors.append(f'Id {id} not in the list of jobs')
                continue
            results = self._parse_result(id)
            if results is not None:
                for index, record in enumerate(results):
                    self._process_one_record(id, index, record)

        library = MediaLibrary(tuple(self.records), tuple(self.errors))
        fname = f'{self.current_job_id}.output.zip'
        library.save(self.cache_folder / fname)
        return fname