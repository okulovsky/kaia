from foundation_kaia.brainbox_utils import run_brainbox_app, InstallingSupport
from service import VideoToImagesService
from installer import VideoToImagesInstaller
from pathlib import Path

if __name__ == '__main__':
    installer = VideoToImagesInstaller(Path('/resources'))
    run_brainbox_app(
        [
            VideoToImagesService(installer),
            InstallingSupport(installer),
        ],
        True
    )
