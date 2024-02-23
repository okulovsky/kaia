
from kaia.brainbox.core import IDecider
from kaia.infra import FileIO
from uuid import uuid4

class FakeDubDecider(IDecider):
    def __init__(self, options_per_job: int = 3):
        self.options_per_job = options_per_job

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, voice: str, text: str):
        result = []
        for i in range(self.options_per_job):
            fname = f'{uuid4()}.json'
            FileIO.write_json(dict(voice=voice, text=text,option_index=i), self.file_cache / fname)
            result.append(fname)
        return result