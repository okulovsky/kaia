from dataclasses import dataclass, field
from threading import Lock
import socket


@dataclass
class DeciderInstance:
    controller: 'IController'
    parameter: str | None
    instance_id: str
    main_port: int
    auxiliary_ports: list[int] = field(default_factory=list)


class InstancesRegistry:
    def __init__(self):
        self._lock = Lock()
        self._instances: dict[str, DeciderInstance] = {}
        self._reserved_ports: set[int] = set()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = Lock()

    def register(self, instance: DeciderInstance) -> None:
        with self._lock:
            self._instances[instance.instance_id] = instance
            self._reserved_ports.discard(instance.main_port)

    def deregister(self, instance_id: str) -> None:
        with self._lock:
            self._instances.pop(instance_id, None)

    def get_instances(self, controller_name: str | None = None) -> list[DeciderInstance]:
        with self._lock:
            values = list(self._instances.values())
        if controller_name is None:
            return values
        return [i for i in values if i.controller.get_name() == controller_name]

    def get_instance(self, instance_id: str) -> DeciderInstance | None:
        with self._lock:
            return self._instances.get(instance_id)

    def count_instances(self, controller_name: str) -> int:
        return len(self.get_instances(controller_name))

    def allocate_port(self, base_port: int = 20000) -> int:
        with self._lock:
            used = {i.main_port for i in self._instances.values()}
            used |= {p for i in self._instances.values() for p in i.auxiliary_ports}
            used |= self._reserved_ports
            port = base_port
            while port in used or not self._port_is_free(port):
                port += 1
            self._reserved_ports.add(port)
            return port

    def release_port(self, port: int) -> None:
        with self._lock:
            self._reserved_ports.discard(port)

    @staticmethod
    def _port_is_free(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False

    def clean_up(self, controller, parameter: str | None) -> None:
        self._kill_same_slot(controller, parameter)
        self._sweep_orphans(controller)

    def _kill_same_slot(self, controller, parameter) -> None:
        from ...deployment import Command
        name = controller.get_container_name(parameter)
        executor = controller.get_executor()
        executor.execute(['docker', 'stop', name], Command.Options(ignore_exit_code=True))
        executor.execute(['docker', 'rm', name], Command.Options(ignore_exit_code=True))
        stale = [i.instance_id for i in self.get_instances(controller.get_name()) if i.parameter == parameter]
        for instance_id in stale:
            self.deregister(instance_id)

    def _sweep_orphans(self, controller) -> None:
        from ...deployment import Command
        known_ids = {i.instance_id for i in self.get_instances(controller.get_name())}
        executor = controller.get_executor()
        for container_id in controller.get_image_source().get_relevant_containers(executor):
            if container_id in known_ids or container_id[:12] in known_ids:
                continue
            executor.execute(['docker', 'stop', container_id], Command.Options(ignore_exit_code=True))
            executor.execute(['docker', 'rm', container_id], Command.Options(ignore_exit_code=True))
