from brainbox.framework.deployment import IContainerRunner, DockerArgumentsHelper, Deployment, LocalImageSource, LocalExecutor
from dataclasses import dataclass
from brainbox.framework import Loc, IExecutor, Command
from pathlib import Path
from .container_builder import create_brainbox_builder

@dataclass
class BrainBoxRunner(IContainerRunner):
    folder: Path
    port: int = 18090
    auto_restart: bool = False
    user_id: str|None = None
    docker_group_id: str|None = None


    def _get_user(self, executor: IExecutor):
        if self.user_id is not None:
            user_id = self.user_id
        else:
            user_id = int(executor.execute(['id','-u'], Command.Options(return_output=True)).strip())
        if self.docker_group_id is not None:
            docker_group_id = self.docker_group_id
        else:
            docker = executor.execute(['getent', 'group', 'docker'], Command.Options(return_output=True)).strip()
            docker_group_id = int(docker.split(':')[2])
        return ['--user', f'{user_id}:{docker_group_id}']


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
            *self._get_user(executor),
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
            create_brainbox_builder()
        )



