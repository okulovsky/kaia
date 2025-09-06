from pathlib import Path
from dataclasses import dataclass
from avatar.server import AvatarApi
import shutil
import os
from yo_fluq import FileIO, fluq, Query
from brainbox.deciders import Collector, InsightFace
from brainbox import BrainBox
from .clustering import Clustering

@dataclass
class FaceIdentificationTraining:
    temp_folder: Path
    avatar_api: AvatarApi
    brainbox_api: BrainBox.Api

    @property
    def pictures_file(self):
        return self.temp_folder/'pictures.json'

    @property
    def recognition_file(self):
        return self.temp_folder/'recognition.json'

    def transfer_pictures_from_avatar_to_brainbox(self):
        pictures = self.avatar_api.file_cache.list('webcam','.png')
        FileIO.write_json(pictures, self.pictures_file)
        for picture in Query.en(pictures).feed(fluq.with_progress_bar()):
            self.brainbox_api.upload(
                picture,
                self.avatar_api.file_cache.download(picture),
            )

    def run_recognition(self):
        builder = Collector.TaskBuilder()
        for file in FileIO.read_json(self.pictures_file):
            builder.append(
                BrainBox.Task.call(InsightFace).analyze(file),
                dict(filename=file)
            )
        task = builder.to_collector_pack('to_array')
        command = BrainBox.Command(
            task,
            BrainBox.Command.Cache(self.recognition_file)
        )
        command.execute(self.brainbox_api)

    def create_clustering(self):
        faces = FileIO.read_json(self.recognition_file)
        faces = [f for f in faces['result'] if len(f['result']) == 1]
        names = tuple(f['tags']['filename'] for f in faces)
        vectors = tuple(f['result'][0]['embedding'] for f in faces)
        return Clustering(self.avatar_api, names, vectors)


