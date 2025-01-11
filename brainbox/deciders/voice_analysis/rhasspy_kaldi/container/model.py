import os
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass
from train import Trainer
from utils import train_path, rhasspy_path
from transcribe import Transcriber


@dataclass
class Model:
    name: str

    def get_path(self):
        return train_path/self.name


    def train(self, base_language: str, sentences: str, custom_words: str):
        shutil.rmtree(self.get_path(), True)
        shutil.copytree(rhasspy_path/base_language, self.get_path())
        trainer = Trainer(self.get_path(), sentences, base_language, custom_words)
        return trainer.train()

    def create_transcriber(self) -> Transcriber:
        return Transcriber(self.get_path())







