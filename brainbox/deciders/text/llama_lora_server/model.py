from pathlib import Path
from ....framework import DownloadableModel, IController
from huggingface_hub import hf_hub_download
from typing import cast


class HFModel(DownloadableModel):
    def __init__(self, hf_repo: str, local_folder: str, filename: str):
        self.hf_repo = hf_repo
        self.local_folder = local_folder
        self.filename = filename

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder(self.local_folder) / self.filename

    def __str__(self):
        return f"<{self.filename} from {self.hf_repo}>"

    @classmethod
    def download(cls, models: list["DownloadableModel"], controller: IController):
        for model in models:
            model = cast(HFModel, model)
            save_path = model.get_local_location(controller)
            hf_hub_download(
                repo_id=model.hf_repo,
                filename=model.filename,
                local_dir=save_path.parent,
            )
