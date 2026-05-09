import os

from chara import Chara, CaseCollection
from .vector_annotation import IVectorAnnotationCase
from dataclasses import dataclass
from typing import Any
import numpy as np
from pathlib import Path

@dataclass
class UserSampleCase(IVectorAnnotationCase):
    file: str
    local_path: Path
    vector: np.ndarray = None
    class_: str|None = None
    annotation: str|None = None
    prior_annotation: str|None = None

    def get_id(self) -> str:
        return self.file

    def get_vector(self) -> np.ndarray:
        return self.vector

    def set_annotation(self, annotation: Any):
        self.annotation = annotation

def _send(bts: bytes, path: Path):
    if not path.is_file():
        path.write_bytes(bts)
    if not Chara.Apis.brainbox_api.cache.is_file(path.name):
        Chara.Apis.brainbox_api.cache.upload(path.name, path)



def collect_from_cache(prefix: str, suffix: str) -> CaseCollection[UserSampleCase]:
    files = Chara.Apis.avatar_api.cache.list('current/', prefix, suffix)
    folder = Chara.current.folder/'files'
    os.makedirs(folder, exist_ok=True)
    cases = []
    for file in files:
        path = folder/file
        _send(path, Chara.Apis.avatar_api.cache.read(path.name))
        cases.append(UserSampleCase(file, path))
    return CaseCollection(cases)


def collect_from_resources(resource: type) -> CaseCollection[UserSampleCase]:
    data = Chara.Apis.avatar_api.resources(resource).list('', glob=True)
    folder = Chara.current.folder/'files'
    cases = []
    os.makedirs(folder, exist_ok=True)
    for file in data:
        split = file.split('/')
        if len(split) != 2:
            continue
        class_, name = split
        path = folder/name
        _send(Chara.Apis.avatar_api.resources(resource).read(file), path)
        cases.append(UserSampleCase(
            name,
            path,
            prior_annotation=class_
        ))
    return CaseCollection(cases)