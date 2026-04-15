from foundation_kaia.brainbox_utils import Installer


class ZonosInstaller(Installer[str]):
    def _execute_installation(self):
        from processing import ZonosModel
        ZonosModel()

    def _execute_unique_model_loading(self):
        from processing import ZonosModel
        return ZonosModel()
