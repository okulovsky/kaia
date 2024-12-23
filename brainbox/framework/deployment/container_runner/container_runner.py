from typing import *
from abc import ABC, abstractmethod
from ..executor import IExecutor

from pathlib import Path
import os
from enum import Enum

class IContainerRunner(ABC):
    @abstractmethod
    def run(self, image_name: str, container_name: str, executor: IExecutor):
        pass




class DockerArgumentsHelper:
    @staticmethod
    def arg_mount(host_path, container_path):
        return f'type=bind,source={host_path},target={container_path}'

    @staticmethod
    def arg_publish_ports(publish_ports: None | dict[int, int]) -> list[str]:
        arguments = []
        for host_port, container_port in publish_ports.items():
            arguments.extend(['--publish', f'{host_port}:{container_port}'])
        return arguments

    @staticmethod
    def arg_mount_folders(mount_folders: None | dict[str | Path, str]) -> list[str]:
        arguments = []
        if mount_folders is not None:
            for host_path, container_path in mount_folders.items():
                arguments.extend(['--mount', DockerArgumentsHelper.arg_mount(host_path, container_path)])
        return arguments

    @staticmethod
    def arg_propagate_env_variables(env_variables: Optional[Iterable[str]]) -> list[str]:
        arguments = []
        if env_variables is not None:
            for variable in env_variables:
                arguments.append('--env')
                arguments.append(f'{variable}={os.environ[variable]}')
        return arguments

    @staticmethod
    def arg_env_variables(*propagate, **set):
        return DockerArgumentsHelper.arg_propagate_env_variables(propagate) + DockerArgumentsHelper.arg_set_env_variables(set)


    @staticmethod
    def arg_set_env_variables(env_variables: None | dict[str, str]):
        arguments = []
        if env_variables is not None:
            for variable, value in env_variables.items():
                arguments.append('--env')
                arguments.append(f'{variable}={value}')
        return arguments
