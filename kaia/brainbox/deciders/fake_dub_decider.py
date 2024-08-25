import json
from kaia.brainbox.core import IDecider, File
from kaia.infra import FileIO
from io import StringIO

class FakeDubDecider(IDecider):
    def __init__(self, options_per_job: int = 3, always_as_array: bool = False):
        self.options_per_job = options_per_job
        self.always_as_array = always_as_array

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, voice: str, text: str):
        result = []
        for i in range(self.options_per_job):
            fname = f'{self.current_job_id}.output.{i}.json'
            io = StringIO()
            json.dump(dict(voice=voice, text=text,option_index=i), io)
            result.append(File(fname, io.getvalue().encode('utf-8')))
        if len(result) == 1 and not self.always_as_array:
            return result[0]
        return result