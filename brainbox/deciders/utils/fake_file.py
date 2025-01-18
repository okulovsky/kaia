from ...framework import IDecider, File
import json
from copy import copy
import time

class FakeFile(IDecider):
    def __call__(self, tags: dict=None, extension_with_dot='', array_length: int|None = None, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        if tags is None:
            tags = {}
        if array_length is None:
            return File(self.current_job_id+'.output'+extension_with_dot, json.dumps(tags))
        else:
            result = []
            for i in range(array_length):
                new_tags = copy(tags)
                new_tags['option_index'] = i
                result.append(File(self.current_job_id+'.output.'+str(i)+extension_with_dot, json.dumps(new_tags)))
            return result


