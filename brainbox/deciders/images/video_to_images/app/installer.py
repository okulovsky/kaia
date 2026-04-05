from foundation_kaia.brainbox_utils import Installer
from pathlib import Path


class VideoToImagesInstaller(Installer[str]):
    def __init__(self, resource_folder: Path):
        super().__init__(resource_folder)

    def _execute_installation(self):
        from layer_semantic_comparator import get_comparator
        get_comparator()
