import os

from avatar.server.components import IAvatarComponent
from avatar.server.components.audio_chunks import WavWriter
import flask
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from yo_fluq import FileIO


@dataclass
class Upload:
    timestamp: datetime
    file_name: str


class PhonixRecordingComponent(IAvatarComponent):
    def __init__(self, folder: Path):
        self.folder = folder
        self.recent_uploads: list[Upload] = []

    def setup_server(self, app: flask.Flask, address: str):
        app.add_url_rule('/phonix-recording/upload/<sample_rate>/<file_name>', view_func=self.phonix_upload, methods=['POST'])

    def phonix_upload(self, sample_rate, file_name):
        stream = flask.request.stream
        sample_rate = int(sample_rate)
        os.makedirs(self.folder, exist_ok=True)
        with open(self.folder/file_name, 'wb') as file:
            writer = WavWriter(file, sample_rate)
            while True:
                buffer = stream.read()
                writer.write_packed(buffer)
                if len(buffer) == 0:
                    break
            writer.close()
        self.recent_uploads.append(Upload(datetime.now(), file_name))
        self.recent_uploads = self.recent_uploads[-50:]
        return "OK"
