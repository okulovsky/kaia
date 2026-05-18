import subprocess
from dataclasses import dataclass
from pathlib import Path
from foundation_kaia.brainbox_utils import Installer
from foundation_kaia.brainbox_utils.training import download_file

COMFYUI_PATH = Path('/home/app/comfy/ComfyUI')


@dataclass
class ComfyUIModel:
    url: str
    models_subfolder: str | None = None
    filename: str | None = None

    def get_filename(self) -> str:
        if self.filename is not None:
            return self.filename
        return self.url.split('/')[-1]

    def get_name(self) -> str:
        return self.get_filename()


@dataclass
class ComfyUIInstallation:
    model: ComfyUIModel | None = None
    component: str | None = None

    def get_name(self) -> str:
        if self.model is not None:
            return self.model.get_name()
        return f'component:{self.component}'


class ComfyUIInstaller(Installer[ComfyUIInstallation]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: ComfyUIInstallation):
        if model_spec.model is not None:
            dest = (
                COMFYUI_PATH / 'models'
                / model_spec.model.models_subfolder
                / model_spec.model.get_filename()
            )
            download_file(model_spec.model.url, dest)
        elif model_spec.component is not None:
            subprocess.run(
                ['comfy', '--skip-prompt', '--workspace', str(COMFYUI_PATH), 'node', 'install', model_spec.component],
                check=True,
            )
