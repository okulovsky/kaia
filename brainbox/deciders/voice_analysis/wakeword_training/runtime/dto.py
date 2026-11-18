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
    report_ru: Path | None = None
    history: Path | None = None
    scores: Path | None = None
    manifest: Path | None = None
    remote_reference: dict[str, Any] | None = None


@dataclass
class FullRunResult:
    status: str
    output: Path
    training: TrainingResult | None = None
    error: str | None = None


from typing import TypedDict


class DatasetRequirements(TypedDict):
    target_variants: list[str]
    minimum_positive_counts: dict[str, int]
    resource_profile: str


class TrainingResultReference(TypedDict):
    training_id: str
    status: str
    request_fingerprint: str
    execution_fingerprint: str
    result_manifest_sha256: str
    archive_sha256: str
    archive_size: int
    model_sha256: str


PortableDatasetManifest = dict[str, Any]
PortableResultManifest = dict[str, Any]
BackgroundResourceProfile = dict[str, Any]
TrainingRequest = dict[str, Any]
TrainingStatus = dict[str, Any]
UnifiedConfiguration = dict[str, Any]
LocalTrainingResult = TrainingResult
