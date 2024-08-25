import shutil
import time
from unittest import TestCase
from kaia.brainbox.deployment import LocalExecutor, IImageSource, IImageBuilder, Deployment, IContainerRunner
from ...core import IInstaller
import requests
from copy import deepcopy
from kaia.infra import Loc

class DockerService:
    def __init__(self,
                 installer: 'IInstaller',
                 ping_port: None|int,
                 startup_timeout_in_seconds: None|int,
                 container_runner: IContainerRunner,
                 ):
        from .docker_installer import DockerInstaller
        if not isinstance(installer, DockerInstaller):
            raise ValueError("installer must be DockerInstaller")
        self._installer = installer
        self._ping_port = ping_port
        self._startup_timeout_in_seconds = startup_timeout_in_seconds
        from .brainbox_runner import BrainBoxServiceRunner
        if not isinstance(container_runner, BrainBoxServiceRunner):
            raise ValueError("container_runner must be BrainBoxServiceRunner")
        self._container_runner: BrainBoxServiceRunner = container_runner
        self._container_runner._installer = installer


    def get_deployment(self):
        return Deployment(
            self._installer._image_source,
            self._container_runner,
            self._installer._executor,
            self._installer._image_builder,
        )


    def is_running(self) -> bool:
        if self._ping_port is None:
            raise ValueError("Can't check running if control port is not set")
        try:
            addr = f'http://{self._container_runner._installer._executor.get_machine().ip_address}:{self._ping_port}'
            reply = requests.get(addr, timeout=1)
        except:
            return False
        if reply.status_code != 200:
            raise ValueError(f"Ping request returned status code {reply.status_code}\n{reply.text}")
        return True

    def wait_for_running(self):
        wait_time = 60 if self._startup_timeout_in_seconds is None else self._startup_timeout_in_seconds
        for i in range(wait_time):
            if self.is_running():
                return
            else:
                time.sleep(1)
        raise ValueError("Coulnd't wait for a service to start")

    def kill(self):
        self.get_deployment().stop()

    def run(self):
        self.get_deployment().stop().remove().run()

    def as_notebook_service(self):
        runner = deepcopy(self._container_runner)
        runner.command_line_arguments=['--notebook']
        runner.publish_ports = {8899:8899}
        runner.mount_data_folder = True
        runner._mount_folders = {Loc.root_folder: '/repo'}
        runner._detach = False
        runner._interactive = False
        return DockerService(
            self._installer,
            None,
            None,
            runner
        )

    def as_service_worker(self, *arguments):
        runner = deepcopy(self._container_runner)
        runner.command_line_arguments = list(arguments)
        runner.publish_ports = {}
        runner.mount_data_folder = True
        runner._detach = False
        runner._interactive = False
        return DockerService(
            self._installer,
            None,
            None,
            runner
        )


