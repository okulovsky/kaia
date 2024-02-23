from typing import *
import copy
import os

from kaia.infra import Loc, FileIO
import subprocess
import time
from dataclasses import dataclass
from yo_fluq import *
from .container import Container
from .simple_pusher import SimpleContainerPusher


@dataclass
class Deployment:
    container: Container
    ssh_url: str
    ssh_username: str
    open_ports: Iterable[int] = (7860,)
    mount_remote_data_folder: Optional[str] = None
    propagate_env_variables: Iterable[str] = ()
    custom_env_variables: Dict[str, str] = None
    additional_arguments: Iterable[str] = ()


    @property
    def pusher(self) -> SimpleContainerPusher:
        return self.container.pusher

    def _ssh(self):
        return [
            'ssh',
            f'{self.ssh_username}@{self.ssh_url}'
        ]

    def _remote_pull(self):
        subprocess.call(self._ssh() + list(self.pusher.get_auth_command()))
        subprocess.call(self._ssh() + ['docker', 'pull', f'{self.pusher.docker_url}/{self.pusher.registry}:latest'])

    def _get_run_local(self, image):
        ports = Query.en(self.open_ports).select_many(lambda z: ['-p', f'{z}:{z}']).to_list()
        args = ['docker', 'run'] + ports + [image]
        return args

    def kill_remote(self):
        reply = subprocess.check_output(self._ssh() +
                                        ['docker',
                                         'ps',
                                         '-q',
                                         '--filter',
                                         f'ancestor={self.pusher.docker_url}/{self.pusher.registry}',
                                         ])
        container = reply.decode('utf-8').strip()
        if container != '':
            subprocess.call(self._ssh() + ['docker', 'stop', container])

    def _get_run(self, image):
        ports = Query.en(self.open_ports).select_many(lambda z: ['-p', f'{z}:{z}']).to_list()
        mount = []
        if self.mount_remote_data_folder is not None:
            mount = ['--mount', f'type=bind,source={self.mount_remote_data_folder},target=/data']

        if self.custom_env_variables is None:
            env_dict = {}
        else:
            env_dict = copy.deepcopy(self.custom_env_variables)
        for var in self.propagate_env_variables:
            env_dict[var] = os.environ[var]

        envs = []
        for var, value in env_dict.items():
            environment_quotation = '"'
            envs.append('--env')
            envs.append(f'{environment_quotation}{var}={value}{environment_quotation}')

        args = ['docker', 'run'] + ports + mount + envs + list(self.additional_arguments) + [image]
        return args

    def run_remote(self):
        self.container.build()
        self.container.push()
        self.kill_remote()
        self._remote_pull()
        if self.mount_remote_data_folder is not None:
            subprocess.call(self._ssh() + ['mkdir', '-p', self.mount_remote_data_folder])
        commands = self._ssh() + self._get_run(f'{self.pusher.docker_url}/{self.pusher.registry}:latest')
        subprocess.call(commands)

