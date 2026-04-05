from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, SmallImageBuilder,
    IImageBuilder, DockerWebServiceController, IModelDownloadingController, DownloadableModel,
)
from .settings import RhasspyKaldiSettings
from .model import RhasspyKaldiModel
from pathlib import Path


class RhasspyKaldiController(
    DockerWebServiceController[RhasspyKaldiSettings],
    IModelDownloadingController,

):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            None
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return RhasspyKaldiModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            None,
            mount_resource_folders={'profiles': '/profiles', 'models': '/models'},
            publish_ports={self.settings.connection.port: 8084}
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return RhasspyKaldiSettings()

    def create_api(self):
        from .api import RhasspyKaldiApi
        return RhasspyKaldiApi()

    def post_install(self):
        self.download_models(self.settings.languages)
        
    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .tests import english, german, english_custom
        yield from english()
        yield from german()
        yield from english_custom()


DOCKERFILE = f'''
FROM rhasspy/rhasspy

RUN /usr/lib/rhasspy/.venv/bin/pip install notebook flask

COPY . /home/app

ENTRYPOINT ["/usr/lib/rhasspy/.venv/bin/python", "/home/app/main.py"] 
'''


