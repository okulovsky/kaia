from kaia.kaia.audio_control.inputs import FakeInput
from kaia.kaia.audio_control.wav_streaming import WavServerSettings, WavApiSettings, WavStreamingTestApi
from kaia.kaia.audio_control.wav_streaming.wav_streaming_server import WavWriter
from unittest import TestCase
from pathlib import Path
from uuid import uuid4
from kaia.infra import FileIO
from io import BytesIO
import wave

class StreamingTestCase(TestCase):
    def test_streaming(self):
        input_file_name = Path(__file__).parent/'files/computer.wav'
        input = FakeInput([input_file_name])
        input.next_buffer()
        input.start()
        with open(input_file_name,'rb') as file:
            with wave.open(file, "rb") as wave_file:
                frame_rate = wave_file.getframerate()
                print(frame_rate)

        api_settings = WavApiSettings(frame_rate, 512)
        server_settings = WavServerSettings()
        file_name = str(uuid4())
        buffer = BytesIO()
        writer = WavWriter(buffer, api_settings.sample_rate, api_settings.frame_length)
        with WavStreamingTestApi(api_settings, server_settings) as api:
            request = api.create_request(file_name, [])
            while not input.is_buffer_empty():
                data = input.read()
                writer.write_raw(data)
                request.add_wav_data(data)
            request.send()

        due_bytes = buffer.getvalue()
        actual_bytes = FileIO.read_bytes(server_settings.folder/file_name)
        self.assertEqual(due_bytes, actual_bytes)
        with open('streaming_test.wav','wb') as stream:
            stream.write(actual_bytes)


