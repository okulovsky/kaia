from ....framework import IPrerequisite, BrainBoxApi, Loc, LocalExecutor, ResourcePrerequisite
from pathlib import Path
import os

class TortoiseTTSUploadPrerequisite(IPrerequisite):
    def __init__(self, voice: str, source_file_path: Path):
        self.voice = voice
        self.source_file_path = source_file_path


    def execute(self, api: BrainBoxApi):
        tmp_file = Loc.temp_folder / 'tortoise_tts_export' / (self.source_file_path.name + '.wav')
        os.makedirs(tmp_file.parent, exist_ok=True)
        LocalExecutor().execute(['ffmpeg', '-i', str(self.source_file_path), '-ar', '22050', str(tmp_file), '-y'])
        ResourcePrerequisite('TortoiseTTS', f'voices/{self.voice}/{self.source_file_path.name}.wav', tmp_file).execute(api)
        os.unlink(tmp_file)