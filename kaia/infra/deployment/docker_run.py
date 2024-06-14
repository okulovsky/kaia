from typing import *
from dataclasses import dataclass, field
from yo_fluq import Query
import os
import copy
from pathlib import Path

@dataclass
class DockerRun:
    open_ports: Iterable[int] = ()
    mapped_ports: Mapping[int,int] = field(default_factory=dict)
    mount_folders: Mapping[Union[str,Path], str] = field(default_factory=dict)
    propagate_env_variables: Iterable[str] = ()
    custom_env_variables: Dict[str, str] = None
    additional_arguments: Iterable[str] = ()
    command_line_arguments: Iterable[str] = ()
    propagate_gpu: bool = False
    daemon: bool = False


    def get_run_command(self, image):
        ports = Query.en(self.open_ports).select_many(lambda z: ['-p', f'{z}:{z}']).to_list()
        for key, value in self.mapped_ports.items():
            ports.extend(['-p', f'{value}:{key}'])

        mount = []
        for key, value in self.mount_folders.items():
            mount.extend(['--mount', f'type=bind,source={key},target={value}'])

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

        gpu_argument = [] if not self.propagate_gpu else ['--gpus','all']
        daemon_argument = [] if not self.daemon else ['-it', '-d']
        args = (
                ['docker', 'run'] +
                ports +
                mount +
                envs +
                gpu_argument +
                daemon_argument +
                list(self.additional_arguments) +
                [image] +
                list(self.command_line_arguments)
        )
        return args



