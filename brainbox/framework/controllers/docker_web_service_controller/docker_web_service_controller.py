from threading import Thread
from ..docker_controller import DockerController, RunConfiguration
from ..architecture import TSettings
from abc import ABC, abstractmethod
from ...common import ApiUtils
from ...deployment import Command

class DockerWebServiceController(DockerController[TSettings], ABC):
    @abstractmethod
    def get_service_run_configuration(self, port: int, parameter: str|None) -> RunConfiguration:
        pass

    @abstractmethod
    def create_api(self, base_url: str):
        pass

    def get_loading_time_in_seconds(self) -> int:
        return 60

    def find_api(self, instance_id: str):
        instance = self.context.instance_registry.get_instance(instance_id)
        if instance is None:
            raise ValueError(f"{instance_id} is not a known running instance of {self.get_name()}")
        api = self.create_api(f'http://127.0.0.1:{instance.main_port}')
        from .docker_web_service_api import DockerWebServiceApi
        if not isinstance(api, DockerWebServiceApi):
            raise ValueError(f"Unexpected type {api} returned, expected an object of DockerWebServiceApi's subclass")
        api.controller = self
        api._container_parameter = instance.parameter
        return api

    def wait_for_boot(self, port: int):
        ApiUtils.wait_for_reply(
            f'http://127.0.0.1:{port}',
            self.get_loading_time_in_seconds(),
            self.get_name()
        )

    def run(self, parameter: str | None = None):
        registry = self.context.instance_registry
        registry.clean_up(self, parameter)

        main_port = registry.allocate_port()
        try:
            cfg = self.get_service_run_configuration(main_port, parameter)
            container_name = self.get_container_name(parameter)
            container_id = self.run_with_configuration(cfg, container_name=container_name)
        except:
            registry.release_port(main_port)
            raise

        log_lines = []
        Thread(
            target=lambda: self.get_executor().execute(
                ['docker', 'logs', '--follow', container_id],
                Command.Options(monitor_output=log_lines.append, ignore_exit_code=True)
            ),
            daemon=True
        ).start()

        try:
            self.wait_for_boot(main_port)
        except Exception as ex:
            registry.release_port(main_port)
            logs = '\n'.join(log_lines) if log_lines else '(no logs captured)'
            raise ValueError(f"Container {container_id} failed to boot. Container logs:\n{logs}") from ex

        aux_ports = [p for p in (cfg.publish_ports or {}) if p != main_port]
        from ..architecture import DeciderInstance
        registry.register(DeciderInstance(self, parameter, container_id, main_port, aux_ports))
        return container_id

    def stop(self, instance_id: str):
        super().stop(instance_id)
        self.context.instance_registry.deregister(instance_id)
