from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Batches:
    items: list[BatchSummary]
    total: int


@dataclass
class BatchSummary:
    batch_id: str
    deciders: list[str]
    received_timestamp: datetime
    finished_timestamp: datetime | None
    total_processing_time: float | None
    progress: float
    tasks_waiting: int
    tasks_in_work: int
    tasks_success: int
    tasks_failure: int
    tasks_total: int
    is_finished: bool
