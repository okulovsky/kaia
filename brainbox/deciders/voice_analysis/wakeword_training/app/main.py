from pathlib import Path

from installer import WakewordTrainingInstaller
from service import WakewordTrainingService

from foundation_kaia.brainbox_utils import InstallingSupport, run_brainbox_app

if __name__ == "__main__":
    installer = WakewordTrainingInstaller(Path("/resources"))
    run_brainbox_app(
        [WakewordTrainingService(installer), InstallingSupport(installer)], True
    )
