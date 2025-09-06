from ....framework import DockerWebServiceApi, FileLike
from .settings import InsightFaceSettings
from .controller import InsightFaceController
import requests

class InsightFace(DockerWebServiceApi[InsightFaceSettings, InsightFaceController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def analyze(self, image: FileLike.Type):
        with FileLike(image, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/analyze',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"InsightFaceApi couldn't analyze\n{reply.text}")
            return reply.json()

    Controller = InsightFaceController
    Settings = InsightFaceSettings
