from pathlib import Path
from kaia.brainbox.deciders.arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from .api import Denoiser
from kaia.brainbox.deployment import SmallImageBuilder

class DenoiserInstaller(LocalImageInstaller):
    def __init__(self, settings):
        self.settings = settings

        service = DockerService(
            self, self.settings.port, self.settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 8084},
                gpu_required=BrainBoxServiceRunner.GpuRequirement.No,
            )
        )

        super().__init__(
            'denoiser',
            Path(__file__).parent / 'container',
            DOCKERFILE,
            DEPENDENCIES,
            service
        )

        self.notebook_service = service.as_notebook_service()

    def create_api(self):
        return Denoiser(f'{self.ip_address}:{self.settings.port}')

DOCKERFILE = f"""
FROM python:3.11-slim-buster

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /app

COPY . /app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

ENTRYPOINT ["python3", "/app/main.py"]
"""

DEPENDENCIES = """
    resemble-enhance
"""
