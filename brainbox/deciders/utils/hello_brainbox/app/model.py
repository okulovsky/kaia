from dataclasses import dataclass

from foundation_kaia.brainbox_utils import Installer, TModelSpec, download_file


@dataclass
class HelloBrainBoxModelSpec:
    url: str


class HelloBrainBoxInstaller(Installer[HelloBrainBoxModelSpec]):
    def _execute_installation(self):
        # Place here actions required for model-independent installation
        pass

    def _execute_model_downloading(self, model: str, model_spec: TModelSpec):
        download_file(model_spec.url, self.resources_folder/'models'/model)

    def _execute_model_loading(self, model: str, model_spec: TModelSpec):
        return f"[LOADED] {self.resources_folder/'models'/model}"
