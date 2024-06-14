from ...core import IDecider
from ....infra import FileIO
from uuid import uuid4

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
            fname = f'{uuid4()}.json'
            FileIO.write_json(dict(prompt=prompt,option_index=i, model=self.fake_model), self.file_cache / fname)
            result.append(fname)
        return result