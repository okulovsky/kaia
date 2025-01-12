from typing import cast
from pathlib import Path

from ....framework import DownloadableModel, File, IController
from dataclasses import dataclass

@dataclass
class WD14TaggerModel(DownloadableModel):
    name: str
    file_name: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder('models')/'hub'/self.file_name

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import WD14TaggerController
        from .api import WD14Tagger
        controller = cast(WD14TaggerController, controller)
        instance_id = controller.run(None)
        api: WD14Tagger = controller.find_api(instance_id)
        file = File.read(Path(__file__).parent/'image.png')
        for model in models:
            model = cast(WD14TaggerModel, model)
            api.interrogate(file, model=model.name)
        controller.stop(instance_id)


