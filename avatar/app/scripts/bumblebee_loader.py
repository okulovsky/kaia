import shutil
from pathlib import Path

_WEB_ROOT = Path(__file__).parents[2] / 'web'


def copy_bumblebee_workers(frontend_folder: Path):
    """
    Copy Porcupine worker files from avatar/web/bumblebee-workers/
    into the frontend folder so they can be served at /frontend/bumblebee-workers/.
    """
    src = _WEB_ROOT / 'bumblebee-workers'
    dst = frontend_folder / 'bumblebee-workers'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
