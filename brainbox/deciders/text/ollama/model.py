from pathlib import Path

from ....framework import DownloadableModel, IController
from typing import cast

class OllamaModel(DownloadableModel):
    def __init__(self, name: str, location: str|None = None):
        self.name = name
        if location is None:
            location = name
            if '/' not in location:
                location='library/'+location
            if ':' in location:
                location = location.replace(':','/')
            else:
                location = location+'/latest'
        self.location = location

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('main') / 'models/manifests/registry.ollama.ai/library' / self.location

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import OllamaController
        controller = cast(OllamaController, controller)
        for model in models:
            model = cast(OllamaModel, model)
            controller.run_auxiliary_configuration(controller.get_service_run_configuration('').as_service_worker('pull', model.name))