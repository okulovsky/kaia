import io
import os.path
import subprocess
import tarfile
import uuid
from pathlib import Path

from foundation_kaia.marshalling import FileLikeHandler
from interface import IPiper, FileLike

MODEL_DIR = Path('/resources/models')
TEMP_DIR = Path('/tmp')


class PiperService(IPiper):
    def voiceover(self,
                  text: str,
                  model: str = 'en',
                  speaker: int | None = None,
                  noise_scale: float | None = None,
                  length_scale: float | None = None,
                  noise_w: float | None = None,
                  ) -> FileLike:
        id = str(uuid.uuid4())
        text_filename = TEMP_DIR / f'{id}.txt'
        audio_path = TEMP_DIR / f'{id}.wav'
        model_path = MODEL_DIR / (model + '.onnx')

        try:
            with open(text_filename, 'w') as f:
                f.write(text)

            command = [f'cat {text_filename} | /lsiopy/bin/piper --model {model_path} --output_file {audio_path}']
            for option, value in [('noise_scale', noise_scale), ('length_scale', length_scale), ('noise_w', noise_w), ('speaker', speaker)]:
                if value is not None:
                    command.append(f' --{option} {value}')
            command = ' '.join(command)

            try:
                subprocess.check_output(["sh", "-c", command])
            except subprocess.CalledProcessError as ex:
                raise ValueError(f"Exception when called\n{command}\n\nThe error: {ex.output}")

            with open(audio_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.isfile(text_filename):
                os.unlink(text_filename)
            if os.path.isfile(audio_path):
                os.unlink(audio_path)



    def upload_tar_voice(self, tar_file: FileLike, name: str | None = None) -> None:
        data = FileLikeHandler.to_bytes(tar_file)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r') as tar:
            onnx_data = None
            json_data = None
            derived_name = None
            for member in tar.getmembers():
                if member.name.endswith('.onnx.json'):
                    json_data = tar.extractfile(member).read()
                elif member.name.endswith('.onnx'):
                    onnx_data = tar.extractfile(member).read()
                    derived_name = Path(member.name).stem

        if onnx_data is None:
            raise ValueError("No .onnx file found in tar archive")
        if json_data is None:
            raise ValueError("No .onnx.json file found in tar archive")

        if name is None:
            name = derived_name

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(MODEL_DIR / f'{name}.onnx', 'wb') as f:
            f.write(onnx_data)
        with open(MODEL_DIR / f'{name}.onnx.json', 'wb') as f:
            f.write(json_data)

    def delete_voice(self, name: str) -> None:
        (MODEL_DIR / f'{name}.onnx').unlink(missing_ok=True)
        (MODEL_DIR / f'{name}.onnx.json').unlink(missing_ok=True)
