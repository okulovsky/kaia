import os
from typing import *
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

@dataclass
class ModelFileInfo:
    class Type(Enum):
        BestModel = 0
        Checkpoint = 1
        Stash = 2

    path: Path
    type: 'ModelFileInfo.Type'
    step: int
    index: int = 0

    @staticmethod
    def _parse_filename(filename: str, parent: Path) -> Optional['ModelFileInfo']:
        original_filename = filename

        if not filename.endswith(_SUFFIX):
            return None
        filename = filename.replace(_SUFFIX,'')

        type = None
        for key, value in _PREFIXES.items():
            if filename.startswith(key):
                filename = filename.replace(key,'')
                type = value
                break
        if type is None:
            return None

        try:
            step = int(filename)
        except:
            return None

        return ModelFileInfo(parent/original_filename, type, step)

    @staticmethod
    def parse_folder(folder: Path, custom_filenames = None) -> List['ModelFileInfo']:
        if custom_filenames is None:
            files = os.listdir(folder)
        else:
            files = custom_filenames
        ar = [m for m in (ModelFileInfo._parse_filename(f, folder) for f in files) if m is not None]
        ar = list(sorted(ar, key = lambda z: -z.step))
        for i in range(len(ar)):
            ar[i].index = i
        return ar




_SUFFIX = '.pth'


_PREFIXES = {
    'best_model_': ModelFileInfo.Type.BestModel,
    'stash_': ModelFileInfo.Type.Stash,
    'checkpoint_': ModelFileInfo.Type.Checkpoint
}
