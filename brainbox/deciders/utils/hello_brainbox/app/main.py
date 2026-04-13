from foundation_kaia.brainbox_utils import run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport, SingleModelStorage
from foundation_kaia.marshalling.amenities import Storage
from model import HelloBrainBoxModelSpec, HelloBrainBoxInstaller
from service import HelloBrainBoxService
from pathlib import Path


if __name__ == '__main__':
    installer = HelloBrainBoxInstaller()
    storage = SingleModelStorage(installer, 'google')
    service = HelloBrainBoxService(storage)
    run_brainbox_app(
        [
            service,
            ModelLoadingSupport(storage),
            ModelInstallingSupport[HelloBrainBoxModelSpec](installer),
        ]
    )




