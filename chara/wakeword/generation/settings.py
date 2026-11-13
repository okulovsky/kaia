import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

GROUPS = ("positive_train", "positive_test", "negative_train", "negative_test")


@dataclass
class GenerationSettings:
    name: str
    target_variants: list[str]
    resource_specs: list[dict]
    language_code: str = "en"
    prefix: str = "Hi "
    suffix: str = " go."
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(GROUPS, 2))
    custom_negative_phrases: list[str] = field(default_factory=list)
    seed: int = 42
    batch_size: int = 16
    min_vosk_confidence: float = 0.7
    augmentation_rounds: int = 1
    augmentation_batch_size: int = 16
    schema_version: int = 2
    synthesis_backend: str = "parler-mini-v1"
    processing_backend: str = "host-v2"
    resource_folder: str = "data/wakeword-resources"

    def validate(self):
        if not isinstance(self.name, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]*", self.name
        ):
            raise ValueError("name must be lowercase snake_case")
        if (
            not isinstance(self.target_variants, list)
            or not self.target_variants
            or any(
                not isinstance(v, str) or not v.strip() for v in self.target_variants
            )
        ):
            raise ValueError("target_variants must contain nonempty strings")
        if self.language_code != "en":
            raise ValueError(
                "this pipeline preserves the English-only adversarial generator"
            )
        if not isinstance(self.counts, dict) or set(self.counts) != set(GROUPS):
            raise ValueError("counts must specify all four groups")
        for value in (
            *self.counts.values(),
            self.batch_size,
            self.augmentation_rounds,
            self.augmentation_batch_size,
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(
                    "counts, rounds and batch sizes must be positive integers"
                )
        if isinstance(self.min_vosk_confidence, bool) or not isinstance(
            self.min_vosk_confidence, (int, float)
        ):
            raise ValueError("confidence must be a number")  # noqa: TRY004 - Preserve the public validation API: invalid settings raise ValueError.
        if (
            not math.isfinite(self.min_vosk_confidence)
            or not 0 <= self.min_vosk_confidence <= 1
        ):
            raise ValueError("confidence must be finite and in [0,1]")
        if (
            type(self.seed) is not int
            or not 0 <= self.seed < 2**32
            or type(self.schema_version) is not int
            or self.schema_version != 2
        ):
            raise ValueError("invalid seed or schema_version")
        if self.seed + 3 * sum(self.counts.values()) > 2**32:
            raise ValueError(
                "seed plus the attempt budget exceeds the supported seed range"
            )
        if (
            self.synthesis_backend != "parler-mini-v1"
            or self.processing_backend != "host-v2"
        ):
            raise ValueError("unsupported backend; use a new host-v2 output")
        if not isinstance(self.resource_folder, str) or not self.resource_folder:
            raise ValueError("resource_folder must be a nonempty path")
        if not isinstance(self.prefix, str) or not isinstance(self.suffix, str):
            raise ValueError("prefix and suffix must be strings")  # noqa: TRY004 - Preserve the public validation API: invalid settings raise ValueError.
        if not isinstance(self.custom_negative_phrases, list) or any(
            not isinstance(v, str) or not v.strip()
            for v in self.custom_negative_phrases
        ):
            raise ValueError("negative phrases must be nonempty strings")
        if not isinstance(self.resource_specs, list):
            raise ValueError("resource_specs must be a list")  # noqa: TRY004 - Preserve the public validation API: invalid settings raise ValueError.
        for spec in self.resource_specs:
            if not isinstance(spec, dict) or not all(
                isinstance(spec.get(k), str) and spec[k]
                for k in ("id", "source", "revision")
            ):
                raise ValueError("resource requires id, source and revision")
            if spec.get("kind") not in (
                "model",
                "phonemizer",
                "mit_rir",
                "background",
                "acav",
                "background_wav",
                "rir_wav",
            ):
                raise ValueError(
                    "unsupported local resource kind; Piper resources are no longer used"
                )
            if spec.get("sha256") is not None and (
                not isinstance(spec["sha256"], str)
                or not re.fullmatch("[0-9a-f]{64}", spec["sha256"])
            ):
                raise ValueError(
                    "resource sha256 must contain 64 lowercase hexadecimal characters"
                )
        return self

    def canonical(self):
        self.validate()
        values = asdict(self)
        values["resource_folder"] = str(Path(self.resource_folder).resolve())
        return json.loads(json.dumps(values, sort_keys=True, allow_nan=False))

    @classmethod
    def read(cls, path: Path):
        path = Path(path).resolve()
        values = json.loads(path.read_text(encoding="utf-8-sig"))
        if "generation" in values:
            values = values["generation"]
        values.pop("_comments", None)
        folder = Path(values.get("resource_folder", "../data/wakeword-resources"))
        values["resource_folder"] = (
            str((path.parent / folder).resolve())
            if not folder.is_absolute()
            else str(folder)
        )
        return cls(**values).validate()
