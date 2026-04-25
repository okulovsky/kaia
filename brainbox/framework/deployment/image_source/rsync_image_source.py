from pathlib import Path
from .image_source import IImageSource
from ..executor import IExecutor
from ..executor.machine import Machine
from ..executor.ssh_executor import SSHExecutor


class RsyncImageSource(IImageSource):
    def __init__(self,
                 image_name: str,
                 local_staging_dir: Path,
                 remote_staging_dir: str,
                 remote_machine: Machine,
                 ):
        self.image_name = image_name
        self.local_staging_dir = Path(local_staging_dir)
        self.remote_staging_dir = remote_staging_dir
        self.remote_machine = remote_machine

    def get_image_name(self):
        return self.image_name

    def push(self, executor: IExecutor):
        self.local_staging_dir.mkdir(parents=True, exist_ok=True)
        executor.execute_shell(f'docker save {self.image_name} | tar -xf - -C {self.local_staging_dir}')

        SSHExecutor(self.remote_machine).execute(['mkdir', '-p', self.remote_staging_dir])
        executor.execute([
            'rsync', '-av', '--delete',
            f'{self.local_staging_dir}/',
            f'{self.remote_machine.username}@{self.remote_machine.ip_address}:{self.remote_staging_dir}/',
        ])

    def pull(self, executor: IExecutor):
        executor.execute_shell(f'tar -cf - -C {self.remote_staging_dir} . | docker load')
