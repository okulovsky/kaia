import json
from kaia.brainbox.core import IDecider, File
from io import StringIO

class FakeImageDecider(IDecider):
    def __init__(self, options_per_job: int = 4):
        self.options_per_job = options_per_job
        self.fake_model = None

    def warmup(self, parameters: str):
        self.fake_model = parameters


    def cooldown(self, parameters: str):
        self.fake_model = None


    def __call__(self, prompt: str):
        result = []
        for i in range(self.options_per_job):
            fname = f'{self.current_job_id}.output.{i}.json'
            io = StringIO()
            json.dump(dict(prompt=prompt, option_index=i, model=self.fake_model), io)
            result.append(File(fname, io.getvalue().encode('utf-8')))
        return result

