from kaia.infra.marshalling_api import MarshallingEndpoint
import requests
from pathlib import Path
from ...core import IApiDecider
from ..arch.utils import FileLike
from ...media_library import MediaLibrary

class Resemblyzer(IApiDecider):
    def __init__(self, address: str, model: str = None):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.model = model

    def _classify(self,
                 model: str,
                 file: str|Path|bytes
                 ):
        with FileLike(file, self.file_cache) as file:
            reply = requests.post(
                f'http://{self.address}/classify/{model}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code == 500:
                raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
            return reply.json()['speaker']

    def __call__(self, file: FileLike.Type):
        return self._classify(self.model, file)


class ResemblyzerExtendedApi(Resemblyzer):
    def __init__(self, address: str):
        super().__init__(address, None)

    def classify(self, model, file: str|Path|bytes):
        return self._classify(model, file)


    def upload_dataset_file(self, model: str, split: str, speaker: str, fname: str,  file: FileLike.Type):
        with FileLike(file, self.file_cache) as file:
            return requests.post(
                f'http://{self.address}/upload_dataset_file/{model}/{split}/{speaker}/{fname}',
                files=(
                    ('file', file),
                )
            ).text

    def upload_dataset(self, model: str, media_library: MediaLibrary):
        for record in media_library:
            self.upload_dataset_file(model, record.tags['split'], record.tags['speaker'], record.filename, record.get_content())


    def delete_dataset(self, model: str):
        return requests.post(
            f'http://{self.address}/delete_dataset/{model}'
        ).text

    def train(self, model):
        reply = requests.post(f'http://{self.address}/train/{model}')
        try:
            return reply.json()
        except:
            raise ValueError(f"Failed to parse JSON\n{reply.text}")
