from foundation_kaia.brainbox_utils import run_brainbox_app, ModelInstallingSupport, InstallingSupport
from service import PiperTrainingService
from installer import PiperTrainingInstaller, PiperTrainingModel
from pathlib import Path

if __name__ == '__main__':
    installer = PiperTrainingInstaller(Path('/resources'))
    run_brainbox_app(
        [
            PiperTrainingService(installer),
            ModelInstallingSupport[PiperTrainingModel](installer),
            InstallingSupport(installer),
        ],
        True
    )