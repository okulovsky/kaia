from typing import *
import subprocess
from .file_io import FileIO
from .loc import Loc
from pathlib import Path

class FFmpegTools:
    @staticmethod
    def concat_audio_with_ffmpeg(paths: Iterable[Path], output_path: Path, keep_temp_file: bool = False):
        control_content_array = [f"file '{p}'" for p in paths]
        control_content = '\n'.join(control_content_array)
        with Loc.create_temp_file('dubber', 'txt', keep_temp_file) as control_path:
            FileIO.write_text(control_content, control_path)

            args = [
                'ffmpeg',
                '-f',
                'concat',
                '-safe',
                '0',
                '-i',
                str(control_path),
                '-y',
                str(output_path)
            ]
            try:
                subprocess.check_output(args)
            except subprocess.CalledProcessError as err:
                raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}. Output\n{err.output}')

    @staticmethod
    def make_video_from_audio_and_image(image_path, audio_file, output):
        subprocess.call(f'ffmpeg -y -loop 1 -i {image_path} -i {audio_file} -c:v libx264 -c:a mp3 -shortest {output} -y')


    @staticmethod
    def create_silence_audio(output_path, duration_in_seconds, sample_rate=22000):
        subprocess.call([
            'ffmpeg',
            '-f',
            'lavfi',
            '-i',
            f'anullsrc=r={sample_rate}:cl=mono',
            '-t',
            str(duration_in_seconds),
            str(output_path)
        ])
        return output_path

