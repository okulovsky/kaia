from dataclasses import dataclass
from foundation_kaia.marshalling_2 import JSON
from typing import Any
from abc import ABC, abstractmethod
from ..job_processing import Job
from datetime import datetime

class IJobRequestFactory(ABC):
    @abstractmethod
    def to_job_request(self) -> 'JobRequest':
        pass

@dataclass
class JobDescription(IJobRequestFactory):
    id: str
    decider: str
    parameter: str|None
    method: str|None
    arguments: dict[str, Any]
    info: JSON
    batch: str|None
    ordering_token: str | None
    dependencies: dict[str,str]

    def to_job_request(self) -> 'JobRequest':
        return JobRequest((self,))

    def to_job(self):
        return Job(
            id = self.id,
            decider = self.decider,
            parameter = self.parameter,
            method = self.method,
            arguments = self.arguments,
            info = self.info,
            batch = self.batch if self.batch else self.id,
            ordering_token = self.ordering_token,
            dependencies = self.dependencies,
            received_timestamp = datetime.now(),
            has_dependencies = len(self.dependencies)>0
        )



class JobRequest(IJobRequestFactory):
    def __init__(self, jobs: tuple[JobDescription, ...]):
        self.jobs = jobs
    
    @property
    def main_id(self) -> str:
        return self.jobs[0].id

    def to_job_request(self) -> 'JobRequest':
        return JobRequest(self.jobs)





