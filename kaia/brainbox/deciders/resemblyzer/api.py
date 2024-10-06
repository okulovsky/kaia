from kaia.infra.marshalling_api import MarshallingEndpoint
import requests
from pathlib import Path
from ...core import IApiDecider
from ..arch.utils import FileLike
from ...media_library import MediaLibrary

class Resemblyzer(IApiDecider):
    def __init__(self, address: str, model: str|None = None):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.model = model

    def set_model(self, model) -> 'Resemblyzer':
        self.model = model
        return self

    def __call__(self, file: FileLike.Type):
        return self.classify(file)


    def classify(self, file: str|Path|bytes):
        with FileLike(file, self.file_cache) as file:
            reply = requests.post(
                f'http://{self.address}/classify/{self.model}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code == 500:
                raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
            return reply.json()['speaker']

    def upload_dataset_file(self, split: str, speaker: str, fname: str,  file: FileLike.Type|None = None):
        if file is None:
            file = fname
        with FileLike(file, self.file_cache) as file:
            return requests.post(
                f'http://{self.address}/upload_dataset_file/{self.model}/{split}/{speaker}/{fname}',
                files=(
                    ('file', file),
                )
            ).text

    def delete_dataset(self):
        return requests.post(
            f'http://{self.address}/delete_dataset/{self.model}'
        ).text

    def train(self):
        reply = requests.post(f'http://{self.address}/train/{self.model}')
        try:
            return reply.json()
        except:
            raise ValueError(f"Failed to parse JSON\n{reply.text}")

    def train_on_media_library(self, media_library_path: Path, append_dataset: bool = False):
        media_library = MediaLibrary.read(media_library_path)
        if not append_dataset:
            self.delete_dataset()
        for record in media_library:
            self.upload_dataset_file(record.tags['split'], record.tags['speaker'], record.filename, record.get_content())
        self.train()
