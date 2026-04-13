from foundation_kaia.marshalling import service, endpoint
from brainbox.framework.controllers.self_test.last_call import LastCallDocumentation
from brainbox.framework.job_processing import OperatorLogItem

@service
class IDiagnosticsService:
    @endpoint(method='GET')
    def last_call(self) -> LastCallDocumentation:
        ...

    @endpoint(method='GET')
    def operator_log(self, entries_count: int|None = 100) -> list[OperatorLogItem]:
        ...


