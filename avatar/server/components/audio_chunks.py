import flask
import time
from datetime import datetime
from pathlib import Path
import os
import wave
from .avatar_component import IAvatarComponent
import struct


class AudioChunksComponent(IAvatarComponent):
    def __init__(self, folder: Path):
        self.folder = folder
        self.audio_chunks = {}

    def setup_server(self, app: flask.Flask):
        app.add_url_rule('/audio-chunks/start', view_func=self.audio_chunks_start, methods=['POST'])
        app.add_url_rule('/audio-chunks/end', view_func=self.audio_chunks_end, methods=['POST'])

    def audio_chunks_start(self):
        client_id = flask.request.form['client_id']
        chunk_index = int(flask.request.form['index'])
        wav_data = flask.request.files['blob'].read()

        audio_data = wav_data[44:]
        self.audio_chunks[client_id].append((chunk_index, audio_data))

        print(f'Chunk {chunk_index}: Client {client_id}, Size: {len(audio_data)} bytes')
        print(f'Current chunks for client {client_id}: {len(self.audio_chunks[client_id])}')

        return {'status': 'ok', 'chunk_index': chunk_index}

    def audio_chunks_end(self):
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
            'wav_path': os.path.join(self.folder, wav_filename),
            'chunks': total_chunks,
            'process_time': process_time
        }

    def _write_combined_wav(self, wav_filename, sample_rate, chunks):
        wav_folder = os.path.join(self.folder)
        wav_path = os.path.join(wav_folder, wav_filename)

        print(f'Creating WAV file: {wav_filename}')

        writer = WavWriter(wav_path, sample_rate=sample_rate)

        try:
            for idx, (chunk_idx, chunk_data) in enumerate(chunks):
                writer.write_packed(chunk_data)
                print(f'Wrote chunk {chunk_idx} ({len(chunk_data)} bytes)')
        finally:
            writer.close()



class WavWriter:
    def __init__(self, file, sample_rate):
        self.wavfile = wave.open(file, 'w')
        self.wavfile.setparams((1, 2, sample_rate, 0, "NONE", "NONE"))

    def write_packed(self, data: bytes):
        self.wavfile.writeframes(data)

    def write_raw(self, data: list[int]):
        data = struct.pack("h" * len(data), *data)
        self.write_packed(data)

    def close(self):
        self.wavfile.close()