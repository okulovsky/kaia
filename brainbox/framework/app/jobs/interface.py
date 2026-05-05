from typing import Any
from foundation_kaia.marshalling import service, endpoint, JSON
from brainbox.framework.task import JobDescription
from brainbox.framework.job_processing import Job
from .dto import JobSummary
from typing import Iterable


@service
class IJobsService:
    @endpoint(method='POST')
    def base_add(self, jobs: list[JobDescription]) -> list[str]:
        """Submits a list of jobs and returns their assigned IDs."""
        ...

    @endpoint(method='POST')
    def base_join(self, ids: list[str], timeout_in_seconds: float|None = None, ignore_errors: bool|None = None) -> list[Any]:
        """Blocks until all specified jobs complete, returning their results."""
        ...

    @endpoint(method='POST')
    def cancel_job(self, job_id: str) -> None:
        """Cancels a single pending job."""
        ...

    @endpoint(method='GET')
    def get_job(self, id: str) -> Job:
        """Returns the full job record including status and result."""
        ...

    @endpoint(method='GET')
    def get_job_summary(self, id: str) -> JobSummary:
        """Returns a brief status summary for a job."""
        ...

    @endpoint
    def get_job_summaries(self, ids: list[str]) -> list[JobSummary]:
        """Returns status summaries for all jobs."""
        ...

    @endpoint
    def get_jobs(self, ids: list[str]) -> Iterable[Job]:
        ...
