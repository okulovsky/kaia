from foundation_kaia.marshalling import service, endpoint
from .dto import JobRecord


@service
class IJobsService:
    @endpoint(method='GET')
    def get_jobs(self, batch_id: str) -> list[JobRecord]:
        ...

    @endpoint(method='POST')
    def cancel_job(self, job_id: str) -> None:
        ...
