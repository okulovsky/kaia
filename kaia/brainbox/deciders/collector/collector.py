import copy
from typing import *
from kaia.brainbox.core import IDecider, FailedJobArgument, File
from kaia.brainbox.media_library import MediaLibrary
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
            if isinstance(result, FailedJobArgument):
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
                    raise ValueError(
                        "To be included in the MediaLibrary, the output of the job must be File, str or list of those")
            for file_index, file in enumerate(result):
                tags_copy = copy.copy(tags)

                inline_kwarg = {}
                if not isinstance(file, File):
                    inline_kwarg['inline_content'] = file

                record = MediaLibrary.Record(
                    filename=file.name,
                    holder_location=self.file_cache,
                    timestamp=datetime.now(),
                    job_id=id,
                    tags=tags_copy,
                    **inline_kwarg
                )
                record.tags['option_index'] = file_index
                records.append(record)
        library = MediaLibrary(tuple(records), tuple(errors))
        fname = f'{self.current_job_id}.output.zip'
        library.save(self.file_cache / fname)
        return fname

    def to_array(self, tags: dict[str, dict], **kwargs):
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



