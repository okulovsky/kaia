from abc import ABC, abstractmethod
from pathlib import Path
from ....framework import DownloadableModel, IController
from huggingface_hub import hf_hub_download
from typing import cast


class HFResource(DownloadableModel, ABC):
    def __init__(self, model_id: str, hf_repo: str, repo_filename: str) -> None:
        self.model_id = model_id
        self.hf_repo = hf_repo
        self.repo_filename = repo_filename

    @abstractmethod
    def get_local_location(self, controller: IController) -> Path:
        pass

    def __str__(self):
        return f"<{self.repo_filename} from {self.hf_repo}>"

    @classmethod
    def download(cls, models: list["DownloadableModel"], controller: IController) -> None:
        for model in models:
            model = cast(HFResource, model)
            save_path = model.get_local_location(controller)
            hf_hub_download(
                repo_id=model.hf_repo,
                filename=model.repo_filename,
                local_dir=save_path.parent,
            )
            (save_path.parent / model.repo_filename).rename(save_path)


class HFModel(HFResource):
    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder("models", self.model_id) / "model.gguf"


class HFLoraAdapter(HFResource):
    def __init__(self, model_id: str, hf_repo: str, repo_filename: str, adapter_name: str) -> None:
        super().__init__(model_id, hf_repo, repo_filename)
        self.local_filename = adapter_name + ".gguf"

    def get_local_location(self, controller: IController) -> Path:
        return (
            controller.resource_folder("models", self.model_id, "lora_adapters")
            / self.local_filename
        )
