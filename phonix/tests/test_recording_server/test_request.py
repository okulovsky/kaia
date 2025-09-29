from phonix.components import PhonixApi
from phonix.daemon.inputs import FakeInput
from avatar.server.components.audio_chunks import WavWriter
from unittest import TestCase
from pathlib import Path
from uuid import uuid4
from yo_fluq import FileIO
from io import BytesIO
from foundation_kaia.misc import Loc


class StreamingTestCase(TestCase):
    def test_streaming(self):
        file = Path(__file__).parent.parent / 'files/computer.wav'
        file_id = str(uuid4())+'.wav'

        input = FakeInput()
        input.set_sample(FileIO.read_bytes(file))
        input.start()

        with (Loc.create_test_folder() as folder):
            with PhonixApi.Test(folder) as api:
                request = api.create_recording_request(file_id, input.current_sample_rate, [])
                packages = []
                while not input.is_buffer_empty():
                    data = input.read()
                    packages.append(data.buffer)
                    request.add_wav_data(data.buffer)

                request.send()
                actual_bytes = api.file_cache.open(file_id)

            buffer = BytesIO()
            writer = WavWriter(buffer, input.current_sample_rate)
            for data in packages:
                writer.write_raw(data)
            writer.close()
            due_bytes = buffer.getvalue()

            self.assertEqual(due_bytes, actual_bytes)



