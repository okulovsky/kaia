import json
import time
from foundation_kaia.marshalling import service, endpoint, ApiCall, HttpMethod, Serializer
from foundation_kaia.logging import SerializableLogItem
from typing import Callable, Iterable
from ....controllers import ControllerLike, ControllerRegistry
from .side_process_pool import ISideProcess, SideProcessPool






@service
class ISideProcessService:
    @endpoint
    def start(self, decider: str) -> str:
        """Launches a side process for the given decider and returns its key."""
        ...

    @endpoint
    def join(self, key: str) -> None:
        """Blocks until the side process identified by key finishes."""
        ...

    @endpoint(method=HttpMethod.GET)
    def html_report(self, key: str) -> str:
        """Returns the HTML execution report for a side process."""
        ...

    @endpoint(method=HttpMethod.GET)
    def follow_report(self, key: str) -> Iterable[SerializableLogItem]:
        """Iteratively returns the report until the side process is finished"""


    @endpoint(method=HttpMethod.GET)
    def is_running(self, key: str) -> bool:
        """Returns True if the side process is still executing."""
        ...

    @endpoint
    def terminate(self, key: str) -> None:
        """Forcibly stops a running side process."""
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
        items = self.pool.get_report(key)
        lines = []
        for item in items:
            ts = item.timestamp
            ts_str = ts.strftime('%H:%M:%S') if ts is not None else '??:??:??'
            lines.append(f'<div><span style="color:#888">{ts_str}</span> {item.to_html()}</div>')
        return ''.join(lines) or '<div>No output yet...</div>'


    def follow_report(self, key: str) -> Iterable[SerializableLogItem]:
        last_emitted = -1
        while True:
            report = self.pool.get_report(key)
            for index in range(last_emitted+1, len(report)):
                yield report[index].to_serializable()
                last_emitted = index
            if not self.pool.is_running(key):
                break
            time.sleep(1)

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

    def follow_report(self, key: str) -> Iterable[SerializableLogItem]:
        return self._internal.follow_report(key)




