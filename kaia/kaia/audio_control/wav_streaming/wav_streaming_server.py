import flask
from pathlib import Path
from dataclasses import dataclass
import struct
import wave
from kaia.common import Loc
import os
import io

@dataclass
class WavServerSettings:
    folder: Path = Loc.data_folder/'wav_streaming'
    port: int = 13000


class WavWriter:
    def __init__(self, file, sample_rate, frame_length):
        self.wavfile = wave.open(file, 'w')
        self.wavfile.setparams((1, 2, sample_rate, frame_length, "NONE", "NONE"))

    def write_packed(self, data: bytes):
        self.wavfile.writeframes(data)

    def write_raw(self, data: list[int]):
        data = struct.pack("h" * len(data), *data)
        self.write_packed(data)

    def close(self):
        self.wavfile.close()



class WavStreamingServer:
    def __init__(self, settings: WavServerSettings):
        self.settings = settings

    def __call__(self):
        os.makedirs(self.settings.folder, exist_ok=True)
        app = flask.Flask(__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/upload/<sample_rate>/<frame_length>/<file_name>', view_func=self.upload, methods=['POST'])
        app.add_url_rule('/download/<file_name>', view_func=self.download, methods=['GET'])
        app.run('0.0.0.0', self.settings.port)

    def index(self):
        return 'OK'

    def upload(self, sample_rate, frame_length, file_name):
        stream = flask.request.stream
        sample_rate = int(sample_rate)
        frame_length = int(frame_length)

        with open(self.settings.folder/file_name, 'wb') as file:
            writer = WavWriter(file, sample_rate, frame_length)
            while True:
                buffer = stream.read()
                writer.write_packed(buffer)
                if len(buffer) == 0:
                    break
            writer.close()

        return "OK"

    def download(self, file_name):
        with open(self.settings.folder/file_name, 'rb') as file:
            return flask.send_file(
                io.BytesIO(file.read()),
                mimetype='application/octet-stream'
            )


    def terminate(self):
        os._exit(0)