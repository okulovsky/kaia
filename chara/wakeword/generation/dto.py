from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ResourceSpec:
    id: str
    source: str
    revision: str
    sha256: str | None = None
    kind: str = ""
    size: int | None = None


@dataclass
class ResourceManifest:
    resources: list[dict]
    versions: dict[str, str] = field(default_factory=dict)


@dataclass
class AudioCase:
    sample_id: str
    lineage_id: str
    class_label: str
    split: str
    seed: int
    attempt_index: int
    text: str
    voice_description: str = ""
    task_ids: dict[str, str] = field(default_factory=dict)
    source_audio: Path | None = None
    recognition: list[dict] | None = None
    verification: Any = None
    crop_audio: Path | None = None
    normalized_audio: Path | None = None
    state: str = "planned"
    error_stage: str | None = None
    reason_code: str | None = None
    error: str | None = None


@dataclass
class GenerationProgress:
    target: int
    reserved_attempts: int = 0
    accepted_ids: list[str] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    pending_task_ids: list[str] = field(default_factory=list)

    @property
    def budget(self):
        return 3 * self.target

    def validate(self):
        if self.target <= 0 or not 0 <= self.reserved_attempts <= self.budget:
            raise ValueError("invalid attempt budget")
        if len(self.accepted_ids) > self.target or set(self.accepted_ids) & set(
            self.rejected_ids
        ):
            raise ValueError("invalid accepted/rejected membership")


@dataclass
class ReviewRecord:
    sample_id: str
    stage: str
    reason_code: str
    expected_text: str
    recognized_text: str = ""
    recognition: list[dict] | None = None
    seed: int = 0
    source_audio: str | None = None
    error: str | None = None


@dataclass
class FeatureArtifact:
    path: str
    shape: tuple[int, ...]
    dtype: str
    sha256: str
    size: int


@dataclass
class RunResult:
    status: str
    effective_settings: dict
    resource_manifest: dict
    progress: dict
    feature_artifacts: dict[str, FeatureArtifact]
    review_path: str
    report_path: str
