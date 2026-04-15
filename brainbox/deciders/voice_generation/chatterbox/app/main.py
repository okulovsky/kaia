import shutil
from foundation_kaia.brainbox_utils import run_brainbox_app, InstallingSupport, UniqueModelStorage
from model import ChatterboxInstaller
from service import ChatterboxService

shutil.copy('/home/app/.local/lib/python3.11/site-packages/chatterbox/mtl_tts.py', '/file_cache/mtl_tts.py')

if __name__ == '__main__':
    installer = ChatterboxInstaller()
    storage = UniqueModelStorage(installer)
    service = ChatterboxService(storage)
    run_brainbox_app([
        service,
        InstallingSupport(installer),
    ])
