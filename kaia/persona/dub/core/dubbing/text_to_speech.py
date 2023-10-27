import pyttsx3
from typing import *
from pathlib import Path
from kaia.infra import Loc
import os
from uuid import uuid4
from .....eaglesong.core import Audio


class TextToSpeech:
    def __init__(self, folder: Optional[Path] = None):
        self.folder = Loc.temp_folder / 'text-to-speech' if folder is None else folder
        os.makedirs(self.folder, exist_ok=True)
        self.engine = pyttsx3.init()

    def dub(self, s: str, path: Optional[Path] = None):
        if path is None:
            path = self.folder / f'{uuid4()}.mp3'
        self.engine.save_to_file(s, str(path))
        self.engine.runAndWait()
        return path

    def dub_to_audio(self, s: str):
        with Loc.temp_file('dubber','wav') as file:
            self.dub(s, file)
            with open(file, 'rb') as stream:
                data = stream.read()
            return Audio(data, s)