import os
from pathlib import Path

from avatar.app import AvatarApi
from foundation_kaia.marshalling import FileLike
from typing import Callable
from yo_fluq import FileIO
import numpy as np
import pandas as pd
from .straregies import IStrategy
from brainbox import BrainBox

def cosine_distances(X, Y):
    X = np.array(X, dtype=float)
    Y = np.array(Y, dtype=float)

    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)

    sim = np.dot(X_norm, Y_norm.T)
    return 1.0 - sim


class VectorIdentificator:
    def __init__(self,
                 api: AvatarApi,
                 folder: Path,
                 strategy: IStrategy,
                 sample_to_vector: Callable[[FileLike], list[float]],
                 ):
        self.api = api
        self.folder = folder
        self.strategy = strategy
        self.sample_to_vector = sample_to_vector
        self.df: pd.DataFrame|None = None
        self.base: dict | None = None

    def _local_file_to_vector(self, path: Path) -> list[float]:
        if not self.api.cache.is_file(path.name):
            self.api.cache.upload(path.name, path)
        return self.sample_to_vector(path.name)

    def _retrieve_content(self, file_id: str) -> bytes:
        return self.api.cache.read(file_id)

    def initialize(self):
        base_file = self.folder/'base.json'
        if not base_file.is_file():
            base = {}
        else:
            base = FileIO.read_json(base_file)

        for class_name in os.listdir(self.folder):
            subfolder = self.folder/class_name
            if not subfolder.is_dir():
                continue
            if class_name not in base:
                base[class_name] = {}
            for file in os.listdir(subfolder):
                file_path = subfolder/file
                if not file_path.is_file():
                    continue
                if file not in base[class_name] or base[class_name][file] is None:
                    vector = self._local_file_to_vector(file_path)
                    base[class_name][file] = vector


        FileIO.write_json(base, base_file)
        array = []
        classes = []
        for class_name, data in base.items():
            for filename, vector in data.items():
                if vector is not None:
                    array.append(vector)
                    classes.append(class_name)
        self.base = base
        self.df = pd.DataFrame(array, index=classes)

    def analyze(self, file: FileLike) -> str|None:
        if self.df is None:
            return None
        vector = self.sample_to_vector(file)
        if vector is None:
            return None
        distances = cosine_distances(self.df.values, np.array(vector).reshape(1, -1)).flatten()
        s = pd.Series(distances, self.df.index)
        winner = self.strategy.get_winner(s)
        return winner

    def add_sample(self, class_name, filename: str):
        content = self._retrieve_content(filename)
        FileIO.write_bytes(
            content,
            self.folder / class_name / filename
        )









