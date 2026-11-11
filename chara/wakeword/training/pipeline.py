"""Host training orchestration with verified, reusable stage boundaries."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..generation.io import read_json, sha256, write_json
from .dependencies import issues, resolve_device, versions
from .dto import TrainingResult
from .inputs import resolve_inputs
from .state import artifact_hashes, fingerprint, run_lock, verify_hashes


class TrainingPipeline:
    def __init__(self, dataset, settings, output, background_manifest=None):
        self.dataset = dataset
        self.settings = settings
        self.root = Path(output).resolve()
        self.background_manifest = background_manifest
        self.stage = "preflight"
        self.arrays = {}
        self.state = None
        self.state_path = self.root / "state.json"

    def run(self):
        try:
            self._preflight()
            with run_lock(self.root):
                cached = self._prepare_output()
                if cached is not None:
                    return cached
                return self._run_stages()
        except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - Preserve pipeline failure diagnostics.
            return self._record_failure(error)
        finally:
            self._close_inputs()

    def _preflight(self):
        self.settings.validate()
        problems = issues()
        if problems:
            raise ValueError("; ".join(problems) + ". Run make setup SCOPE=training")
        self.device = resolve_device(self.settings.device)
        self.snapshot, self.arrays = resolve_inputs(
            self.dataset, self.background_manifest
        )
        self.canonical = self.settings.canonical()
        self.identity = {
            "settings": self.canonical,
            "snapshot": self.snapshot,
            "resolved_device": self.device,
            "versions": versions(),
        }
        self.expected = fingerprint(self.identity)

    def _prepare_output(self):
        self.state_path = self.root / "state.json"
        if self.state_path.exists():
            self.state = read_json(self.state_path)
            if self.state["fingerprint"] != self.expected:
                raise ValueError(
                    "training config/data/backend/versions changed; choose a new output folder"
                )
            verify_hashes(self.root, self.state["input_hashes"])
            for hashes in self.state["completed_stages"].values():
                verify_hashes(self.root, hashes)
            if (self.root / "manifest.json").exists():
                marker = read_json(self.root / "manifest.json")
                verify_hashes(self.root, marker["hashes"], allow_missing_report=True)
                if (
                    not (self.root / "report.html").exists()
                    or not (self.root / "report_ru.html").exists()
                ):
                    from .reporting import write_report

                    write_report(self.root)
                    marker["hashes"]["report.html"] = sha256(self.root / "report.html")
                    marker["hashes"]["report_ru.html"] = sha256(
                        self.root / "report_ru.html"
                    )
                    write_json(self.root / "manifest.json", marker)
                return TrainingResult(
                    "complete",
                    self.root,
                    self.root / (self.settings.model_name + ".onnx"),
                    self.root / "report.html",
                    self.root / "metrics.json",
                )
            if "training" not in self.state["completed_stages"]:
                raise ValueError(
                    "optimizer loop was interrupted; choose a new output folder, reuse the same dataset"
                )
        else:
            self._initialize_output()

    def _initialize_output(self):
        if any(p.name != ".wakeword.lock" for p in self.root.iterdir()):
            raise ValueError(
                "output is not an empty training directory; choose a new output folder"
            )
        write_json(self.root / "config.json", self.canonical)
        write_json(self.root / "data-snapshot.json", self.snapshot)
        self.state = {
            "schema_version": 1,
            "run_id": uuid4().hex,
            "fingerprint": self.expected,
            "status": "preflight",
            "current_stage": "preflight",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "requested_device": self.settings.device,
            "resolved_device": self.device,
            "execution_versions": self.identity["versions"],
            "completed_stages": {},
            "optimizer_updates": 0,
            "input_hashes": artifact_hashes(
                self.root, [self.root / "config.json", self.root / "data-snapshot.json"]
            ),
        }
        write_json(self.state_path, self.state)

    def _execute(self, name, function, files):
        from chara import Chara

        self.stage = name
        if name in self.state["completed_stages"]:
            return
        self.state.update(status=name, current_stage=name, error_stage=None, error=None)
        write_json(self.state_path, self.state)
        Chara.start(self.root / "stages" / name)
        value = Chara.call(function, name)()
        paths = list(files())
        self.state["completed_stages"][name] = artifact_hashes(self.root, paths)
        if name == "training":
            self.state.update(value)
        write_json(self.state_path, self.state)

    def _export_model(self):
        from itertools import chain

        from .batches import row_batches
        from .export import export_model
        from .validation import parity_sample

        sample, indices = parity_sample(self.arrays, self.snapshot, self.settings)
        batches = chain(
            *(
                row_batches(self.arrays[name], self.settings.validation_batch_size)
                for name in ("positive_features_test", "negative_features_test")
            )
        )
        check = export_model(
            self.model, self.model_path, sample, self.settings, batches
        )
        indices["supervised_policy"] = "all validation rows, checked in bounded batches"
        check.update(
            final_state_sha256=sha256(self.root / "final-state.pt"),
            parity_sample_indices=indices,
        )
        write_json(self.root / "export-check.json", check)

    def _write_reports(self):
        from chara import Chara

        from .reporting import write_report

        self.stage = "reporting"
        self.state.update(status=self.stage, current_stage=self.stage)
        write_json(self.state_path, self.state)
        Chara.start(self.root / "stages" / "reporting")
        Chara.call(lambda: str(write_report(self.root)), "reporting")()
        if (
            not (self.root / "report.html").exists()
            or not (self.root / "report_ru.html").exists()
        ):
            write_report(self.root)

    def _publish_result(self):
        hashes = dict(self.state["input_hashes"])
        for values in self.state["completed_stages"].values():
            hashes.update(values)
        hashes["report.html"] = sha256(self.root / "report.html")
        hashes["report_ru.html"] = sha256(self.root / "report_ru.html")
        verify_hashes(self.root, hashes)
        self.state.update(
            status="complete",
            current_stage="complete",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        write_json(self.state_path, self.state)
        write_json(
            self.root / "manifest.json",
            {
                "schema_version": 1,
                "status": "complete",
                "run_id": self.state["run_id"],
                "fingerprint": self.expected,
                "mode": self.settings.mode,
                "hashes": hashes,
            },
        )
        return TrainingResult(
            "complete",
            self.root,
            self.model_path,
            self.root / "report.html",
            self.root / "metrics.json",
        )

    def _run_stages(self):
        self._initialize_model()
        self._train_and_select()
        self._export_and_evaluate()
        self._write_reports()
        return self._publish_result()

    def _record_failure(self, error):
        if self.state is not None and self.stage != "preflight":
            self.state.update(
                status="interrupted"
                if isinstance(error, KeyboardInterrupt)
                else "failed",
                error_stage=self.stage,
                error=str(error),
            )
            write_json(self.root / "state.json", self.state)
        return TrainingResult(
            "failed", self.root, error_stage=self.stage, error=str(error)
        )

    def _close_inputs(self):
        for array in self.arrays.values():
            mapping = getattr(array, "_mmap", None)
            if mapping is not None and (not mapping.closed):
                mapping.close()

    def _initialize_model(self):
        import torch

        from .model import WakewordModel

        torch.set_num_threads(self.settings.num_threads)
        torch.manual_seed(self.settings.seed)
        if self.device == "cuda":
            torch.cuda.manual_seed_all(self.settings.seed)
        self.model = WakewordModel()

    def _train_and_select(self):
        from .checkpoints import select_state
        from .trainer import train

        def training():
            return train(
                self.model,
                self.arrays,
                self.snapshot,
                self.settings,
                self.root,
                self.device,
            )

        self._execute(
            "training",
            training,
            lambda: [
                self.root / "history.jsonl",
                self.root / "last-trained.pt",
                self.root / "checkpoints/index.json",
                *sorted((self.root / "checkpoints").glob("*.pt")),
            ],
        )
        self._execute(
            "selecting",
            lambda: (
                select_state(
                    self.root, read_json(self.root / "checkpoints/index.json")
                ),
                None,
            )[1],
            lambda: [
                self.root / "final-state.pt",
                self.root / "checkpoint-selection.json",
            ],
        )

    def _export_and_evaluate(self):
        import torch

        from .validation import evaluate

        self.model.load_state_dict(
            torch.load(
                self.root / "final-state.pt", map_location="cpu", weights_only=True
            )
        )
        self.model_path = self.root / (self.settings.model_name + ".onnx")
        self._execute(
            "exporting",
            self._export_model,
            lambda: [self.model_path, self.root / "export-check.json"],
        )
        self._execute(
            "evaluating",
            lambda: evaluate(
                self.model_path, self.arrays, self.snapshot, self.settings, self.root
            ),
            lambda: [
                self.root / "metrics.json",
                *sorted((self.root / "scores").glob("*.npy")),
            ],
        )


def run_training(dataset, settings, output, background_manifest=None):
    return TrainingPipeline(dataset, settings, output, background_manifest).run()
