from typing import *
import subprocess
from yo_fluq import FileIO
from ...framework import IDecider


class Ffmpeg(IDecider):
    def concat(self,
               files: Iterable[str],
               target_extension: str = ".wav"
               ):
        paths = [self.cache_folder/file for file in files]
        control_content_array = [f"file '{p}'" for p in paths]
        control_content = '\n'.join(control_content_array)
        temp_file = self.cache_folder/(self.current_job_id+'.txt')
        FileIO.write_text(control_content, temp_file)
        output_file = self.cache_folder/(self.current_job_id+target_extension)
        args = [
            'ffmpeg',
            '-f',
            'concat',
            '-safe',
            '0',
            '-i',
            str(temp_file),
            '-y',
            str(output_file)
        ]
        try:
            subprocess.check_output(args)
            return output_file.name
        except subprocess.CalledProcessError as err:
            raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}. Output\n{err.output}')

    def make_video_from_audio_and_image(
            self,
            image: str,
            audio: str,
            target_extension: str = '.mp4'
    ):
        output_filename = self.current_job_id+target_extension
        subprocess.call([
            'ffmpeg',
            '-y',
            '-loop',
            '1',
            '-i',
            str(self.cache_folder/image),
            '-i',
            str(self.cache_folder/audio),
            '-c:v',
            'libx264',
            '-c:a',
            'mp3',
            '-shortest',
            str(self.cache_folder/output_filename),
            '-y'
        ])
        return output_filename

    def create_silence_audio(self, duration_in_seconds: int = 1, sample_rate: int = 22000, target_extension=".wav"):
        output_filename = self.current_job_id+target_extension
        subprocess.call([
            'ffmpeg',
            '-f',
            'lavfi',
            '-i',
            f'anullsrc=r={sample_rate}:cl=mono',
            '-t',
            str(duration_in_seconds),
            str(self.cache_folder/output_filename)
        ])
        return output_filename

