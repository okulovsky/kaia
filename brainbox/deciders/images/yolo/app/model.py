import shutil
from pathlib import Path

from foundation_kaia.brainbox_utils import Installer


class YoloInstaller(Installer[str]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: str):
        from huggingface_hub import hf_hub_download
        repo_id, file_name = model.split(':')
        hf_dir = self.resources_folder / 'hf'
        hf_dir.mkdir(parents=True, exist_ok=True)
        path_to_cache = hf_hub_download(repo_id=repo_id, filename=file_name, cache_dir=str(hf_dir))
        dest = self.resources_folder / 'models' / repo_id / file_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path_to_cache, str(dest))

    def _execute_model_loading(self, model: str, model_spec: str):
        from ultralytics import YOLO
        repo_id, file_name = model.split(':')
        path = str(self.resources_folder / 'models' / repo_id / file_name)
        yolo = YOLO(path)
        try:
            yolo.to("cuda")
        except Exception:
            yolo.to("cpu")
        return yolo
