from typing import *
from kaia.infra import deployment
from ...core import IInstaller
import time
import requests


class DockerBasedInstallerEndpoint:
    def __init__(self,
                 installer: 'DockerBasedInstaller',
                 run_config: deployment.DockerRun,
                 timeout: int = 0,
                 control_port: int|None = None,
                 ip_address: str = '127.0.0.1'
                 ):
        self._installer = installer
        self._run_config = run_config
        self._timeout = timeout
        self._control_port = control_port
        self._ip_address = ip_address




    def get_run_config(self):
        return self._run_config

    def get_deployment(self):
        return deployment.Deployment(
            self._installer._container_builder,
            self._installer._pusher,
            self._run_config,
            self._installer.executor
        )

    def run(self):
        if self._control_port is not None:
            try:
                requests.get(f'http://{self._ip_address}:{self._control_port}', timeout=1)
                return
            except:
                pass

        self.get_deployment().run()
        if self._control_port is None:
            time.sleep(self._timeout)
        else:
            for i in range(self._timeout):
                try:
                    reply = requests.get(f'http://{self._ip_address}:{self._control_port}')
                    if reply.status_code!=200:
                        raise ValueError(f"Can't up the endpoint: status code of the reply was {reply.status_code}")
                    return
                except:
                    time.sleep(1)
            raise ValueError(f'Service failed to boot up within {self._timeout}')




    def kill(self):
        self.get_deployment().kill()


class DockerBasedInstaller(IInstaller):
    def __init__(self,
                 container_builder: deployment.IContainerBuilder,
                 pusher: Optional[deployment.IContainerPusher] = None
                 ):
        self._container_builder = container_builder
        self._pusher = pusher if pusher is not None else deployment.ExistingLocalContainerPusher(self._container_builder.get_local_name())


    def is_installed(self) -> bool:
        output = self.executor.execute(['docker','images','-q', self._pusher.get_remote_name()], deployment.ExecuteOptions(return_output=True))
        return len(output) > 0

    def create_api(self):
        raise NotImplementedError()

    def uninstall(self):
        deployment.Deployment.kill_by_ancestor_name(self.executor, self._pusher.get_ancestor())
        output = self.executor.execute(['docker','images','-q', self._pusher.get_remote_name()], deployment.ExecuteOptions(return_output=True))
        image = output.decode('utf-8').strip()
        if len(output) > 0:
            self.executor.execute(['docker','image','rm','-f',image])

    def build(self):
        self._container_builder.build_container()
        local_exec = deployment.LocalExecutor()
        local_exec.execute_several(self._pusher.get_push_command(self._container_builder.get_local_name()))

    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        raise NotImplementedError()




    def run_in_any_case_and_return_api(self):
        self.install_if_not_installed()
        self.get_service_endpoint().run()
        return self.create_api()




