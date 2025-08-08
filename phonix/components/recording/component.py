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
        app.add_url_rule('/phonix-recording', view_func=self.phonix_index, methods=['GET'], caption="Browse uploaded sound files")
        app.add_url_rule('/phonix-recording/play/<filename>', view_func=self.phonix_play, methods=['GET'])

    def phonix_index(self):
        html=['<html><body><table>']
        for item in reversed(self.recent_uploads):
            html.append(f'<tr><td>{item.timestamp}</td><td>{item.file_name}</td>')
            html.append(f'<td><audio controls><source src="/phonix-recording/play/{item.file_name}" type="audio/wav"></audio></td>')
            html.append('</tr>')
        html.append("</table></body></html>")
        return ''.join(html)

    def phonix_play(self, filename):
        wav_bytes = FileIO.read_bytes(self.folder/filename)
        return flask.Response(
            wav_bytes,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"'
            }
        )

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
