import shutil
import subprocess
from kaia.brainbox import BrainBoxApi, BrainBoxTask
from kaia.brainbox.deciders import OpenTTS
from pathlib import Path
from kaia.infra import Loc
from kaia.infra.ffmpeg import FFmpegTools
import os
import re

class TestSpeaker:
    def __init__(self,
                 brainbox_api: BrainBoxApi,
                 cache_folder: Path|None = None,
                 remake_everything: bool = False,
                 copy_to_bb_folder: bool = True
                 ):
        self.copy_to_bb_folder = copy_to_bb_folder
        self.brainbox_api = brainbox_api
        if cache_folder is None:
            cache_folder = Loc.temp_folder/'test_speaker'
        self.cache_folder = cache_folder
        self.remake_everything = remake_everything
        os.makedirs(self.cache_folder, exist_ok=True)

    def _get_speaker_path_and_task(self, text: str, speaker: int|str|None = None):
        if speaker is None:
            speaker = 'p256'
        elif isinstance(speaker, int):
            speaker = f'p{256 + speaker}'
        os_friendly_text = re.sub(r'[^a-zA-Z0-9 ]', '', text).replace(' ', '_')
        filename = self.cache_folder / f'{speaker}___{os_friendly_text}.wav'
        task = BrainBoxTask.call(OpenTTS).voiceover(text=text, speakerId=speaker).to_task()
        return speaker, filename, task

    def get_path(self, text: str, speaker: int|str|None = None):
        return self._get_speaker_path_and_task(text, speaker)[1]

    def _from_cache(self, filename):
        if self.copy_to_bb_folder:
            new_file_name = self.brainbox_api.cache_folder/(BrainBoxTask.safe_id()+".wav")
            shutil.copyfile(filename, new_file_name)
            return new_file_name.name
        else:
            return filename


    def speak(self, text: str, speaker: int|str|None = None):
        speaker, filename, task = self._get_speaker_path_and_task(text, speaker)
        if filename.is_file() and not self.remake_everything:
            return self._from_cache(filename)
        file = self.brainbox_api.execute(task)
        shutil.copyfile(self.brainbox_api.cache_folder/file.name, filename)
        return file.name

    def silence(self, duration_in_seconds: int, sample_rate: int = 22050):
        filename = self.cache_folder/f'silence___{duration_in_seconds}.wav'
        if not filename.is_file():
            subprocess.call([
                'ffmpeg',
                '-f',
                'lavfi',
                '-i',
                f'anullsrc=r={sample_rate}:cl=mono',
                '-t',
                str(duration_in_seconds),
                filename
            ])
        return self._from_cache(filename)






