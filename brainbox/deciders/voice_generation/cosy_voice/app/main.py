import sys
import os

sys.path.append('/home/app/repo/')
sys.path.append('/home/app/repo/third_party/Matcha-TTS')
os.environ["MODELSCOPE_CACHE"] = "/resources/modelscope"

from foundation_kaia.brainbox_utils import (
    run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport,
    InstallingSupport, SingleModelStorage
)
from model import CosyVoiceInstaller
from service import CosyVoiceService


if __name__ == '__main__':
    installer = CosyVoiceInstaller()
    storage = SingleModelStorage(installer, default_model='Fun-CosyVoice3-0.5B-2512')
    service = CosyVoiceService(storage)
    run_brainbox_app(
        [
            service,
            ModelLoadingSupport(storage),
            ModelInstallingSupport[str](installer),
            InstallingSupport(installer)
        ]
    )
