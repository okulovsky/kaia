import requests
from pathlib import Path
from ....framework import DockerWebServiceApi, FileLike, BrainBoxApi, MediaLibrary, ResourcePrerequisite, CombinedPrerequisite
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


    def distances(self, file: FileLike.Type, model: str):
        with FileLike(file, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/distances/{model}',
                files = (
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
            return reply.json()


    def train(self, model: str):
        reply = requests.post(f'http://{self.address}/train/{model}')
        if reply.status_code != 200:
            raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
        return reply.json()

    def vector(self, file:FileLike.Type):
        with FileLike(file, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/vector',
                files = (
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Resemblyzer threw an error\n{reply.text}")
            return reply.json()

    @staticmethod
    def upload_dataset_file(model: str, split: str, speaker: str, file: FileLike.Type) -> ResourcePrerequisite:
        fname = FileLike.get_name(file, True)
        return ResourcePrerequisite(
            Resemblyzer,
            f'datasets/{model}/{split}/{speaker}/{fname}',
            file
        )


    @staticmethod
    def delete_dataset(model: str) -> ResourcePrerequisite:
        return ResourcePrerequisite(
            Resemblyzer,
            f'datasets/{model}',
            None
        )

    @staticmethod
    def upload_dataset(model: str, media_library_path: Path, append_dataset: bool = False) -> CombinedPrerequisite:
        command = []
        media_library = MediaLibrary.read(media_library_path)
        if not append_dataset:
            command.append(Resemblyzer.delete_dataset(model))
        for record in media_library:
            command.append(Resemblyzer.upload_dataset_file(
                model,
                record.tags['split'],
                record.tags['speaker'],
                record.get_file()
            ))
        return CombinedPrerequisite(command)


    Controller = ResemblyzerController
    Settings = ResemblyzerSettings
