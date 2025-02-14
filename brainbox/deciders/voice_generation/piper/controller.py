from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, IModelDownloadingController, File, DownloadableModel
)
from .settings import PiperSettings
from pathlib import Path
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .model import PiperModel

class PiperController(
    DockerWebServiceController[PiperSettings],
    IModelDownloadingController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return PiperModel

    def post_install(self):
        self.download_models(self.settings.models_to_download)

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'models' : '/models',
                'cache' : '/cache'
            },
            dont_rm=True
        )

    def get_default_settings(self):
        return PiperSettings

    def create_api(self):
        from .api import Piper
        return Piper()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Piper

        task = BrainBoxTask.call(Piper).voiceover(
            text=VOICEOVER_TEXT,
            model="en",
        )
        result_file = api.execute(task)
        yield TestReport.last_call(api).result_is_file(File.Kind.Audio).href('href')
        check_if_its_sound(api.open_file(result_file).content, tc)




DOCKERFILE = f'''
FROM lscr.io/linuxserver/piper:latest

RUN apt-get update \
 && apt-get install -y python3 python3-pip \
 && apt-get install -y python3 python3-pip wget \
 && rm -rf /var/lib/apt/lists/*

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app


COPY server.py server.py
COPY main.py main.py

ENTRYPOINT ["python3", "/home/app/main.py"]
'''

DEPENDENCIES = '''
annotated-types==0.7.0
anyio==4.8.0
certifi==2024.12.14
charset-normalizer==3.4.1
click==8.1.8
fastapi==0.115.6
h11==0.14.0
idna==3.10
pydantic==2.10.5
pydantic_core==2.27.2
requests==2.32.3
sniffio==1.3.1
starlette==0.41.3
typing_extensions==4.12.2
urllib3==2.3.0
uvicorn==0.34.0
wheel==0.45.1
wyoming==1.1.0
wyoming-piper==1.4.0
'''


ORIGINAL_DEPENDENCIES = '''
fastapi
uvicorn
pydantic
requests
'''