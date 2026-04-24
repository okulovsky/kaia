from dataclasses import dataclass
from foundation_kaia.marshalling import JSON
from typing import Any
from abc import ABC, abstractmethod
from ..job_processing import Job
from datetime import datetime
from uuid import uuid4

class IJobRequestFactory(ABC):
    @abstractmethod
    def to_job_request(self) -> 'JobRequest':
        pass

@dataclass(kw_only=True)
class JobDescription(IJobRequestFactory):
    decider: str
    arguments: dict[str, Any]
    id: str|None = None
    parameter: str|None = None
    method: str|None = None
    info: JSON = None
    batch: str|None = None
    ordering_token: str | None = None
    dependencies: dict[str,str]|None = None

    def to_job_request(self) -> 'JobRequest':
        return JobRequest((self,))

    def to_job(self):
        return Job(
            id = self.id if self.id else str(uuid4()),
            decider = self.decider,
            parameter = self.parameter,
            method = self.method,
            arguments = self.arguments,
            info = self.info,
            batch = self.batch if self.batch else self.id,
            ordering_token = self.ordering_token,
            dependencies = self.dependencies if self.dependencies else {},
            received_timestamp = datetime.now(),
            has_dependencies = (0 if not self.dependencies else len(self.dependencies))>0,
        )



class JobRequest(IJobRequestFactory):
    def __init__(self, jobs: tuple[JobDescription, ...]):
        self.jobs = jobs
    
    @property
    def main_id(self) -> str:
        return self.jobs[0].id

    def to_job_request(self) -> 'JobRequest':
        return JobRequest(self.jobs)





