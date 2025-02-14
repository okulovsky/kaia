from pathlib import Path
import subprocess
import os
from converter import Converter
import pickle


def concat_with_mpeg(temp_file, output_path, paths):
    control_content_array = [f"file '{p}'" for p in paths]
    control_content = '\n'.join(control_content_array)
    with open(temp_file, 'w') as stream:
        stream.write(control_content)

    args = [
        'ffmpeg',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        str(temp_file),
        '-y',
        str(output_path)
    ]
    try:
        subprocess.check_output(args)
    except subprocess.CalledProcessError as err:
        raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}. Output\n{err.output}')


def train(voice: str, converter: Converter):
    source_folder = Path(f'/voices/{voice}/')
    paths = [source_folder/f for f in os.listdir(source_folder)]
    temp_wav = f'/temp/{voice}.wav'
    concat_with_mpeg('files.tmp', temp_wav, paths)
    os.unlink('files.tmp')
    model = converter.convert(temp_wav)
    with open(f'/models/{voice}', 'wb') as stream:
        pickle.dump(model, stream)








