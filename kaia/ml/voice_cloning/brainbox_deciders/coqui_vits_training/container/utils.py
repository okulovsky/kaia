from typing import *
import zipfile
import pickle
from dataclasses import dataclass
from pathlib import Path
import os

import subprocess, sys

@dataclass
class Record:
    filename: str
    content: bytes
    voice: str
    text: str

def get_working_folder(folder):
    folders = os.listdir(folder)
    folders = [z for z in folders if z!='phoneme_cache']
    if len(folders) == 0:
        raise ValueError(f"Cant find working folder inside {folder}")
    elif len(folders) > 1:
        raise ValueError(f"Cant find working folder inside {folder}, too many folders there")
    models_folder = folder / folders[0]
    return models_folder



def read_media_library(media_library_path) -> Iterable[Record]:
    with zipfile.ZipFile(media_library_path, 'r') as zip:
        records = pickle.loads(zip.read('description.pkl'))
        for filename, record in records.items():
            if not record['tags']['selected']:
                continue
            name = filename.replace('.wav', '')
            voice = record['tags']['voice']
            text = record['tags']['text']
            content = zip.read(filename)
            yield Record(name, content, voice, text)


@dataclass
class TrainingState:
    has_data: bool
    has_config: bool
    config_path: Path | None


    def run_continue(self):
        subprocess.call([sys.executable, '-m', 'TTS.bin.train_tts', '--continue_path', str(self.config_path.parent)])


def get_current_training_state(
        dataset_path: Path,
        training_path: Path) -> TrainingState:

    dataset_path = Path(dataset_path)
    training_path = Path(training_path)

    has_data = dataset_path.is_dir()

    config_path = None
    if training_path.is_dir():
        working_dir = get_working_folder(training_path)
        config_path = working_dir/'config.json'
        if not config_path.is_file():
            raise ValueError(f'A unique training folder was found at {config_path.parent}, but without config.json')

    if config_path is not None and not has_data:
        raise ValueError("Misconfiguration: the training was started, but the data is now absent")

    return TrainingState(
        has_data,
        config_path is not None,
        config_path
    )



