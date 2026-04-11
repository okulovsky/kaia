from pathlib import Path
from .scripts_compilation import compile
from .files import copy_files
from .model_loader import download_vosk_model

_WEB_SRC = Path(__file__).parents[2] / 'web' / 'src'

def compile_frontend(frontend_folder: Path):
    compile(_WEB_SRC, frontend_folder / 'scripts')
    copy_files(_WEB_SRC.parent / 'files', frontend_folder / 'system-sounds')
    download_vosk_model(frontend_folder / 'models')