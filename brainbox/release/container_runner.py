from brainbox.framework.deployment import IContainerRunner, DockerArgumentsHelper, Deployment, LocalImageSource, LocalExecutor
from dataclasses import dataclass
from brainbox.framework import Loc, IExecutor
from pathlib import Path
from .container_builder import create_builder

@dataclass
class BrainBoxRunner(IContainerRunner):
    folder: Path
    port: int = 18090
    auto_restart: bool = False

    def run(self, image_name: str, container_name: str, executor: IExecutor):
        restart = ['--restart', 'unless-stopped'] if self.auto_restart else []

        command = [
            'docker',
            'run',
            '--name',
            container_name,
            '--mount',
            DockerArgumentsHelper.arg_mount(self.folder, self.folder),
            '--network',
            'host',
            '--detach',
            '-v',
            '/var/run/docker.sock:/var/run/docker.sock',
            *restart,
            image_name,
            '--data-folder',
            str(self.folder),
            '--port',
            str(self.port)
        ]
        executor.execute(command)

    def get_deployment(self):
        return Deployment(
            LocalImageSource('brainbox'),
            self,
            LocalExecutor(),
            create_builder()
        )



