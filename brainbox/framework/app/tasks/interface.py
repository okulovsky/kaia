from typing import Any
from foundation_kaia.marshalling import service, endpoint, JSON
from brainbox.framework.task import JobDescription
from brainbox.framework.job_processing import Job
from .dto import JobSummary


@service
class ITasksService:
    @endpoint(method='POST')
    def base_add(self, jobs: list[JobDescription]) -> list[str]:
        ...

    @endpoint(method='POST')
    def base_join(self, ids: list[str], timeout_in_seconds: float|None = None, ignore_errors: bool|None = None) -> list[Any]:
        ...

    @endpoint(method='GET')
    def get_job(self, id: str) -> Job:
        ...

    @endpoint(method='GET')
    def get_result(self, id: str) -> Any:
        ...

    @endpoint(method='GET')
    def get_job_summary(self, id: str) -> JobSummary:
        ...

    @endpoint(method='GET')
    def get_summaries(self) -> list[JobSummary]:
        ...

    @endpoint(method='GET')
    def get_info(self, id: str) -> JSON:
        ...

    @endpoint(method='GET')
    def get_error(self, id: str) -> str|None:
        ...

    @endpoint(method='GET')
    def get_log(self, id: str) -> list[str]|None:
        ...
