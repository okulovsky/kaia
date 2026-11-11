"""Versioned, explicit training configuration."""

import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TrainingSettings:
    schema_version: int = 1
    model_name: str = "wakeword"
    seed: int = 42
    device: str = "cpu"
    num_threads: int = 2
    mode: str = "smoke"
    stage_steps: list = field(default_factory=lambda: [8, 4, 4])
    stage_learning_rates: list = field(default_factory=lambda: [1e-4, 1e-5, 1e-6])
    batch_counts: dict = field(
        default_factory=lambda: {
            "positive": 2,
            "adversarial_negative": 2,
            "background": 4,
        }
    )
    accumulation_examples: int = 8
    max_negative_weight: float = 10.0
    target_window_fp_per_hour: float = 0.5
    threshold: float = 0.5
    validations_per_stage: int = 20
    validation_start_fractions: list = field(default_factory=lambda: [0.75, 0.0, 0.0])
    validation_batch_size: int = 4096
    export_atol: float = 1e-5
    export_rtol: float = 1e-4
    recipe_version: str = "notebook-28-v1"
    selection_version: str = "percentiles-v1"
    background_version: str = "segmented-windows-v1"

    @classmethod
    def read(cls, path):
        values = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if "training" in values:
            values = values["training"]
        values.pop("_comments", None)
        return cls(**values).validate()

    def validate(self):
        def integer(x):
            return type(x) is int and x > 0

        def finite(x):
            return type(x) in (int, float) and math.isfinite(x)

        if self.schema_version != 1 or type(self.schema_version) is not int:
            raise ValueError("unsupported training schema_version")
        if self.device not in ("cpu", "auto", "cuda") or self.mode not in (
            "smoke",
            "production",
        ):
            raise ValueError("invalid training device/mode")
        if not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*", self.model_name
        ) or self.model_name.upper().split(".")[0] in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *[f"COM{i}" for i in range(1, 10)],
            *[f"LPT{i}" for i in range(1, 10)],
        }:
            raise ValueError("model_name must be a safe file name")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be uint32")
        if set(self.batch_counts) != {"positive", "adversarial_negative", "background"}:
            raise ValueError("batch_counts requires three classes")
        for value in [
            self.num_threads,
            self.accumulation_examples,
            self.validations_per_stage,
            self.validation_batch_size,
            *self.batch_counts.values(),
        ]:
            if not integer(value):
                raise ValueError("counts must be positive integers, not bool")
        for values in (
            self.stage_steps,
            self.stage_learning_rates,
            self.validation_start_fractions,
        ):
            if not isinstance(values, (list, tuple)) or len(values) != 3:
                raise ValueError("exactly three stages are required")
        if not all(integer(v) for v in self.stage_steps):
            raise ValueError("stage_steps must be positive integers")
        if not all(
            finite(v) and v > 0
            for v in [
                *self.stage_learning_rates,
                self.max_negative_weight,
                self.export_atol,
                self.export_rtol,
            ]
        ):
            raise ValueError(
                "learning rates, weights and tolerances must be finite and positive"
            )
        if not all(
            finite(v) and 0 <= v <= 1
            for v in [self.threshold, *self.validation_start_fractions]
        ):
            raise ValueError("threshold/fractions must be finite and in [0,1]")
        if (
            not finite(self.target_window_fp_per_hour)
            or self.target_window_fp_per_hour < 0
        ):
            raise ValueError("target window rate must be finite and nonnegative")
        if self.validations_per_stage > 20:
            raise ValueError("at most 20 validation events per stage")
        if (self.recipe_version, self.selection_version, self.background_version) != (
            "notebook-28-v1",
            "percentiles-v1",
            "segmented-windows-v1",
        ):
            raise ValueError("unsupported training policy version")
        return self

    def canonical(self):
        self.validate()
        return asdict(self)
