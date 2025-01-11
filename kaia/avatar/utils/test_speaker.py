import shutil
import subprocess
from brainbox import BrainBoxApi, BrainBoxTask
from yo_fluq import FileIO
from brainbox.deciders import OpenTTS
from pathlib import Path
from kaia.common import Loc
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


    def _from_cache(self, filename):
        if self.copy_to_bb_folder:
            new_file_name = BrainBoxTask.safe_id()+".wav"
            self.brainbox_api.upload(new_file_name, FileIO.read_bytes(filename))
            return new_file_name
        else:
            return filename


    def speak(self, text: str, speaker: int|str|None = None, return_cache_path: bool = False):
        speaker, filename, task = self._get_speaker_path_and_task(text, speaker)
        if filename.is_file() and not self.remake_everything:
            if return_cache_path:
                return filename
            else:
                return self._from_cache(filename)
        file = self.brainbox_api.execute(task)
        self.brainbox_api.download(file, filename, True)
        if return_cache_path:
            return filename
        else:
            return file


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






