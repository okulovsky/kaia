from foundation_kaia.marshalling_2 import service, endpoint, ApiCall, HttpMethod
from typing import Callable
from threading import Thread
from ....controllers import ControllerLike, ControllerRegistry
from .side_process_pool import ISideProcess, SideProcessPool

@service
class ISideProcessService:
    @endpoint
    def start(self, decider: str) -> str:
        ...

    @endpoint
    def join(self, key: str) -> None:
        ...

    @endpoint(method=HttpMethod.GET)
    def html_report(self, key: str) -> str:
        ...

    @endpoint(method=HttpMethod.GET)
    def is_running(self, key: str) -> bool:
        ...

    @endpoint
    def terminate(self, key: str) -> None:
        ...


class SideProcessService(ISideProcessService):
    def __init__(self, pool: SideProcessPool, decider_to_side_process: Callable[[str], ISideProcess]):
        self.pool = pool
        self.decider_to_side_process = decider_to_side_process

    def start(self, decider: str) -> str:
        if self.pool.active_processes() > 0:
            raise ValueError("Only one active process is allowed")
        process = self.decider_to_side_process(decider)
        key = self.pool.start(process)
        return key

    def join(self, key: str) -> None:
        return self.pool.join(key)

    def html_report(self, key: str) -> str:
        return self.pool.get_report(key)

    def is_running(self, key: str) -> bool:
        return self.pool.is_running(key)

    def terminate(self, key: str) -> None:
        self.pool.terminate(key)



class SideProcessInternalApi(ISideProcessService):
    def __init__(self, base_url: str, prefix: str | None = None):
        ApiCall.define_endpoints(self, base_url, ISideProcessService, prefix)


class SideProcessApi:
    def __init__(self, base_url: str, prefix: str | None = None):
        self._internal = SideProcessInternalApi(base_url, prefix)

    def start(self, decider: ControllerLike) -> str:
        return self._internal.start(ControllerRegistry.to_controller_name(decider))

    def join(self, key: str) -> None:
        return self._internal.join(key)

    def html_report(self, key: str) -> str:
        return self._internal.html_report(key)

    def terminate(self, key: str) -> None:
        return self._internal.terminate(key)

    def execute(self, decider: ControllerLike) -> None:
        key = self.start(decider)
        self.join(key)




