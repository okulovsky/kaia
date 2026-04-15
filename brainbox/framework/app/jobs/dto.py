from dataclasses import dataclass
from datetime import datetime


@dataclass
class JobRecord:
    id: str
    batch: str
    decider: str
    received_timestamp: datetime
    accepted_timestamp: datetime | None
    finished_timestamp: datetime | None
    in_queue: float | None
    in_work: float | None
    status: str
    progress: float | None
    error: str | None
