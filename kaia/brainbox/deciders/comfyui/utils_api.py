from kaia.brainbox.core import IDecider
from .installer import ComfyUIInstaller
from yo_fluq_ds import Query
from pathlib import Path
import os

class ComfyUIUtils(IDecider):
    def __init__(self, installer: ComfyUIInstaller):
        self.installer = installer

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def get_models(self, subfolder: str|None = None):
        result = []
        models_folder = self.installer._models_folder
        if subfolder is not None:
            models_folder /= subfolder
        for path in Query.folder(models_folder,'**/*'):
            result.append(dict(
                file = str(path.relative_to(models_folder)),
                modification_time = os.path.getmtime(path)
            ))
        return result