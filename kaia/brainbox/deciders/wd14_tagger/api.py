from ..arch.utils import FileLike
import requests
from ...core import IApiDecider

class WD14Tagger(IApiDecider):
    def __init__(self, address):
        self.address = address

    def interrogate(self, image: FileLike.Type, threshold=0.35, model='wd14-vit.v2'):
        with FileLike(image, self.file_cache) as file:
            reply = requests.post(
                f'http://{self.address}/interrogate/{model}/{threshold}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"WD14Tagger couldn't interrogate for {model}\n{reply.text}")
            return reply.json()

    def tags(self, model = 'wd14-vit.v2'):
        reply = requests.post(f'http://{self.address}/tags/{model}')
        if reply.status_code != 200:
                raise ValueError(f"WD14Tagger couldn't get tags for {model}\n{reply.text}")
        return reply.json()

