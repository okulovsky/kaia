"""Results are small metadata objects; arrays remain disk backed."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

DatasetSnapshot = dict[str, Any]
HistoryEvent = dict[str, Any]
CheckpointSelection = dict[str, Any]
ExportCheck = dict[str, Any]
ValidationResult = dict[str, Any]


@dataclass
class TrainingResult:
    status: str
    output: Path
    model: Path | None = None
    report: Path | None = None
    metrics: Path | None = None
    error_stage: str | None = None
    error: str | None = None


@dataclass
class FullRunResult:
    status: str
    output: Path
    training: TrainingResult | None = None
    error: str | None = None
