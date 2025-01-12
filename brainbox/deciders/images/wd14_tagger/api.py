from ....framework import DockerWebServiceApi, FileLike
from .settings import WD14TaggerSettings
from .controller import WD14TaggerController
from .model import WD14TaggerModel
import requests

class WD14Tagger(DockerWebServiceApi[WD14TaggerSettings, WD14TaggerController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def interrogate(self, image: FileLike.Type, threshold=0.35, model='wd14-vit.v2'):
        with FileLike(image, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/interrogate/{model}/{threshold}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"WD14Tagger couldn't interrogate for {model}\n{reply.text}")
            return reply.json()

    def tags(self, model = 'wd14-vit.v2', count=None):
        reply = requests.post(f'http://{self.address}/tags/{model}', json=dict(count=count))
        if reply.status_code != 200:
                raise ValueError(f"WD14Tagger couldn't get tags for {model}\n{reply.text}")
        return reply.json()

    Controller = WD14TaggerController
    Settings = WD14TaggerSettings
    Model = WD14TaggerModel