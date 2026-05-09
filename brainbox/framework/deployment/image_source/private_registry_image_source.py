from .image_source import IImageSource
from ..executor import IExecutor
from ..executor.machine import Machine
from ..executor.ssh_executor import SSHExecutor


class PrivateRegistryImageSource(IImageSource):
    def __init__(self,
                 image_name: str,
                 remote_machine: Machine,
                 registry_port: int = 5000,
                 ):
        self.image_name = image_name
        self.remote_machine = remote_machine
        self.registry_port = registry_port

    def get_image_name(self):
        return self.image_name

    def _remote_tag(self):
        return f'{self.remote_machine.ip_address}:{self.registry_port}/{self.image_name}'

    def push(self, executor: IExecutor):
        executor.execute(['docker', 'tag', self.image_name, self._remote_tag()])
        executor.execute(['docker', 'push', self._remote_tag()])

    def pull(self, executor: IExecutor):
        executor.execute(['docker', 'pull', f'localhost:{self.registry_port}/{self.image_name}'])
        executor.execute(['docker', 'tag', f'localhost:{self.registry_port}/{self.image_name}', self.image_name])
