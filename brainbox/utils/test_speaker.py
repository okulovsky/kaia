import os
import shutil
import uuid

import numpy as np

from brainbox import BrainBox
from brainbox.framework import Loc
import hashlib
from pathlib import Path
from .wav_processor import WavProcessor
from brainbox.deciders import OpenTTS
from yo_fluq import FileIO


class TestSpeaker:
    def __init__(self,
                 api: BrainBox.Api,
                 speaker: int|str|None = None):
        self.api = api
        if speaker is None:
            speaker = 'p256'
        elif isinstance(speaker, int):
            speaker = f'p{256 + speaker}'
        self.speaker = speaker
        self.parts = []
        self.cache_folder = Loc.temp_folder/'test_speaker_cache'


    def speak(self, text: str) -> 'TestSpeaker':
        self.parts.append(text)
        return self

    def pause(self, duration: float = 1) -> 'TestSpeaker':
        self.parts.append(duration)
        return self

    def _produce_file(self) -> Path:
        total = '#'.join(str(i) for i in self.parts)
        filename = hashlib.sha256(total.encode()).hexdigest()[:24]
        path = self.cache_folder/filename
        if path.is_file():
            return path

        text_frames = []
        wav_processor = None
        for part in self.parts:
            if isinstance(part, str):
                result = self.api.execute(BrainBox.Task.call(OpenTTS).voiceover(part, speakerId=self.speaker))
                file = self.api.open_file(result)
                wav_processor = WavProcessor(file.content)
                text_frames.append(wav_processor.frames)

        if wav_processor is None:
            raise ValueError("Test speaker must have some text")

        all_frames = []
        for part in self.parts:
            if isinstance(part, str):
                all_frames.append(text_frames.pop(0))
            else:
                all_frames.append(wav_processor.create_silence(part))

        resulting_frames = np.vstack(all_frames)
        bts = wav_processor.frames_to_wav_bytes(resulting_frames)
        os.makedirs(path.parent, exist_ok=True)
        FileIO.write_bytes(bts, path)
        self.parts = []
        return path

    def to_brain_box(self):
        path = self._produce_file()
        fname = str(uuid.uuid4())+'.wav'
        self.api.upload(fname, path)
        return fname

    def to_file(self, path: Path):
        src_path = self._produce_file()
        shutil.move(src_path, path)

















