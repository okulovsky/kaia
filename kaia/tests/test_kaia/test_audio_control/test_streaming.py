from kaia.kaia.audio_control.wav_streaming import WavServerSettings, WavApiSettings, WavStreamingApi
from kaia.kaia.audio_control.wav_streaming.wav_streaming_server import WavWriter
from unittest import TestCase
from pathlib import Path
from uuid import uuid4
from yo_fluq import FileIO
from io import BytesIO


class StreamingTestCase(TestCase):
    def test_streaming(self):
        file = Path(__file__).parent / 'files/computer.wav'
        frame_rate = WavStreamingApi.get_file_framerate(file)
        api_settings = WavApiSettings(frame_rate, 512)
        server_settings = WavServerSettings()
        file_id = str(uuid4())+'.wav'


        with WavStreamingApi.Test(api_settings, server_settings) as api:
            packages = api.send_file_right_away_and_return_sent_bytes(
                input_file_name=file,
                target_file_id=file_id
            )
            pass
        actual_bytes = FileIO.read_bytes(server_settings.folder/file_id)


        buffer = BytesIO()
        writer = WavWriter(buffer, api_settings.sample_rate, api_settings.frame_length)
        for data in packages:
            writer.write_raw(data)
        writer.close()
        due_bytes = buffer.getvalue()


        self.assertEqual(due_bytes, actual_bytes)



