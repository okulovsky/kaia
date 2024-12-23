
import requests
from pathlib import Path
from ....framework import DockerWebServiceApi, FileLike, BrainBoxApi
from .settings import ResemblyzerSettings
from .controller import ResemblyzerController


class Resemblyzer(DockerWebServiceApi[ResemblyzerSettings, ResemblyzerController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def __call__(self, file: FileLike.Type, model: str):
        return self.classify(file, model)


    def classify(self, file: str|Path|bytes, model: str):
        with FileLike(file, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/classify/{model}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
            return reply.json()['speaker']

    def train(self, model: str):
        reply = requests.post(f'http://{self.address}/train/{model}')
        if reply.status_code != 200:
            raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
        return reply.json()

    @staticmethod
    def upload_dataset_file(api: BrainBoxApi, model: str, split: str, speaker: str, file: FileLike.Type|None = None):
        with FileLike(file, api.cache_folder) as stream:
            fname = FileLike.get_name(file, True)
            api.controller_api.upload_resource(
                Resemblyzer,
                f'datasets/{model}/{split}/{speaker}/{fname}',
                stream.getvalue()
            )

    @staticmethod
    def delete_dataset(api: BrainBoxApi, model: str):
        api.controller_api.delete_resource(
            Resemblyzer,
            f'datasets/{model}',
            True
        )

    Controller = ResemblyzerController
    Settings = ResemblyzerSettings
