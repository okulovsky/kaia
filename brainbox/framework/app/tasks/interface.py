from typing import Any
from foundation_kaia.marshalling import service, endpoint, JSON
from brainbox.framework.task import JobDescription
from brainbox.framework.job_processing import Job
from .dto import JobSummary


@service
class ITasksService:
    @endpoint(method='POST')
    def base_add(self, jobs: list[JobDescription]) -> list[str]:
        """Submits a list of jobs and returns their assigned IDs."""
        ...

    @endpoint(method='POST')
    def base_join(self, ids: list[str], timeout_in_seconds: float|None = None, ignore_errors: bool|None = None) -> list[Any]:
        """Blocks until all specified jobs complete, returning their results."""
        ...

    @endpoint(method='GET')
    def get_job(self, id: str) -> Job:
        """Returns the full job record including status and result."""
        ...

    @endpoint(method='GET')
    def get_result(self, id: str) -> Any:
        """Returns the result payload of a completed job."""
        ...

    @endpoint(method='GET')
    def get_job_summary(self, id: str) -> JobSummary:
        """Returns a brief status summary for a job."""
        ...

    @endpoint(method='GET')
    def get_summaries(self) -> list[JobSummary]:
        """Returns status summaries for all jobs."""
        ...

    @endpoint(method='GET')
    def get_info(self, id: str) -> JSON:
        """Returns the structured info dict attached to a job."""
        ...

    @endpoint(method='GET')
    def get_error(self, id: str) -> str|None:
        """Returns the error message if the job failed, or None."""
        ...

    @endpoint(method='GET')
    def get_log(self, id: str) -> list[str]|None:
        """Returns the execution log lines for a job."""
        ...
