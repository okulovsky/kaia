from pathlib import Path
import os

class ResourceFolder:
    def __init__(self, root: Path):
        self._root = root

    def __call__(self, *subfolders):
        folder = self._root
        for subfolder in subfolders:
            if subfolder is not None:
                folder /= subfolder
        os.makedirs(folder, exist_ok=True)
        return folder
