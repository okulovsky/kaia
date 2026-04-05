from pathlib import Path
from foundation_kaia.marshalling_2 import IComponent
from foundation_kaia.marshalling_2.amenities import StaticFilesComponent
from .compilation import compile
from .files import copy_files
from .model_loader import download_vosk_model

_WEB_SRC = Path(__file__).parents[2] / 'web' / 'src'


class ScriptsComponent(IComponent):
    def __init__(self, folder: Path, compile_on_mount: bool = True):
        self.folder = folder
        self.compile_on_mount = compile_on_mount

    @staticmethod
    def compile(dst_folder: Path):
        compile(_WEB_SRC, dst_folder / 'scripts')
        copy_files(_WEB_SRC.parent / 'files', dst_folder / 'system-sounds')
        download_vosk_model(dst_folder / 'models')

    def mount(self, app):
        if self.compile_on_mount:
            ScriptsComponent.compile(self.folder)
        StaticFilesComponent(self.folder, '/frontend').mount(app)
