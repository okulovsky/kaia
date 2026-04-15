from foundation_kaia.brainbox_utils import run_brainbox_app, SingleModelStorage, ModelLoadingSupport, ModelInstallingSupport
from model import InsightFaceModelSpec, InsightFaceInstaller
from service import InsightFaceService


if __name__ == '__main__':
    installer = InsightFaceInstaller()
    storage = SingleModelStorage(installer, default_model='buffalo_l')
    service = InsightFaceService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[InsightFaceModelSpec](installer),
    ])
