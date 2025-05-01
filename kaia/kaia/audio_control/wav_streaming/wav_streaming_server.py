import flask
from pathlib import Path
from dataclasses import dataclass
import struct
import wave
from kaia.common import Loc
import os
import io
from datetime import datetime

from flask_cors import CORS
from datetime import datetime
import time
from collections import defaultdict


@dataclass
class WavServerSettings:
    folder: Path = Loc.data_folder/'wav_streaming'
    port: int = 13000

@dataclass
class Upload:
    timestamp: datetime
    file_name: str



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
        self.recent_uploads: list[Upload] = []

        self.audio_chunks = defaultdict(list)

    def __call__(self):
        os.makedirs(self.settings.folder, exist_ok=True)
        os.makedirs(os.path.join(self.settings.folder, 'recording', 'wav'), exist_ok=True)

        app = flask.Flask(__name__)

        CORS(app)

        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/upload/<sample_rate>/<frame_length>/<file_name>', view_func=self.upload, methods=['POST'])
        app.add_url_rule('/download/<file_name>', view_func=self.download, methods=['GET'])
        app.add_url_rule('/audio', view_func=self.handle_audio_chunk, methods=['POST'])
        app.add_url_rule('/audio_end', view_func=self.handle_audio_end, methods=['POST'])

        app.run('0.0.0.0', self.settings.port)

    def index(self):
        html=['<html><body><table>']
        for item in reversed(self.recent_uploads):
            html.append(f'<tr><td>{item.timestamp}</td><td>{item.file_name}</td></tr')
        html.append("</table></body></html>")
        return ''.join(html)

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
        self.recent_uploads.append(Upload(datetime.now(), file_name))
        self.recent_uploads = self.recent_uploads[-50:]

        return "OK"

    def download(self, file_name):
        with open(self.settings.folder/file_name, 'rb') as file:
            return flask.send_file(
                io.BytesIO(file.read()),
                mimetype='application/octet-stream'
            )

    def handle_audio_chunk(self):
        client_id = flask.request.form['client_id']
        chunk_index = int(flask.request.form['index'])
        wav_data = flask.request.files['blob'].read()
        
        audio_data = wav_data[44:]
        self.audio_chunks[client_id].append((chunk_index, audio_data))
        
        print(f'Chunk {chunk_index}: Client {client_id}, Size: {len(audio_data)} bytes')
        print(f'Current chunks for client {client_id}: {len(self.audio_chunks[client_id])}')
        
        return {'status': 'ok', 'chunk_index': chunk_index}

    def handle_audio_end(self):
        start_time = time.time() * 1000
        
        client_id = flask.request.form['client_id']
        print(f'\nProcessing end request for client {client_id}')
        print(f'Available clients: {list(self.audio_chunks.keys())}')
        
        if client_id not in self.audio_chunks:
            print(f'Error: No chunks found for client {client_id}')
            return {'status': 'error', 'message': 'No audio chunks found for client'}
        
        chunks = sorted(self.audio_chunks[client_id], key=lambda x: x[0])
        total_chunks = len(chunks)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_filename = f'{client_id}_{timestamp}.wav'
        
        sample_rate = 48000

        try:
            self._write_combined_wav(wav_filename, sample_rate, chunks)
        except Exception as e:
            print(f'Error during processing: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        
        del self.audio_chunks[client_id]
        
        end_time = time.time() * 1000
        process_time = end_time - start_time
        
        return {
            'status': 'ok',
            'wav_filename': wav_filename,
            'wav_path': os.path.join(self.settings.folder, wav_filename),
            'chunks': total_chunks,
            'process_time': process_time
        }

    def _write_combined_wav(self, wav_filename, sample_rate, chunks):
        wav_folder = os.path.join(self.settings.folder)
        wav_path = os.path.join(wav_folder, wav_filename)
        
        print(f'Creating WAV file: {wav_filename}')
        
        writer = WavWriter(wav_path, sample_rate=sample_rate, frame_length=0)
        
        try:
            for idx, (chunk_idx, chunk_data) in enumerate(chunks):
                writer.write_packed(chunk_data)
                print(f'Wrote chunk {chunk_idx} ({len(chunk_data)} bytes)')
        finally:
            writer.close()

    def terminate(self):
        os._exit(0)