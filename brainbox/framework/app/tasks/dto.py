from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brainbox.framework.job_processing.core.job import Job


@dataclass
class JobSummary:
    id: str
    decider: str
    parameter: str|None
    method: str|None
    batch: str|None
    ordering_token: str|None
    received_timestamp: datetime
    ready_timestamp: datetime|None
    assigned_timestamp: datetime|None
    accepted_timestamp: datetime|None
    progress: float|None
    responding_timestamp: datetime|None
    finished_timestamp: datetime|None
    success: bool
    last_update_timestamp: datetime


    @staticmethod
    def from_job(job: 'Job') -> 'JobSummary':
        return JobSummary(
            id=job.id,
            decider=job.decider,
            parameter=job.parameter,
            method=job.method,
            batch=job.batch,
            ordering_token=job.ordering_token,
            received_timestamp=job.received_timestamp,
            ready_timestamp=job.ready_timestamp,
            assigned_timestamp=job.assigned_timestamp,
            accepted_timestamp=job.accepted_timestamp,
            progress=job.progress,
            responding_timestamp=job.responding_timestamp,
            finished_timestamp=job.finished_timestamp,
            success=job.success,
            last_update_timestamp=job.last_update_timestamp,
        )

    @property
    def ready(self) -> bool:
        return self.ready_timestamp is not None

    @property
    def assigned(self) -> bool:
        return self.assigned_timestamp is not None

    @property
    def accepted(self) -> bool:
        return self.accepted_timestamp is not None

    @property
    def finished(self) -> bool:
        return self.finished_timestamp is not None
