import copy
from typing import *
from ....framework import IDecider, FailedJobArgument, File, MediaLibrary
from datetime import datetime
from .collector_to_media_library_convertor import CollectorToMediaLibraryConvertor
from .task_builder import TaskBuilder
from .functional_task_builder import FunctionalTaskBuilder

class Collector(IDecider):

    def to_media_library(self, tags: Dict[str, Dict], **kwargs):
        return CollectorToMediaLibraryConvertor(self.current_job_id, self.cache_folder, tags, kwargs).convert()


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


    TaskBuilder = TaskBuilder
    FunctionalTaskBuilder = FunctionalTaskBuilder
