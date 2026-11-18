"""Readable Chara orchestration for independent remote training."""

from pathlib import Path
from uuid import uuid4

from brainbox.deciders.voice_analysis.wakeword_training.runtime.dto import (
    TrainingResult,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    write_json,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.locking import run_lock
from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
    FILES,
    identity,
    validate_dataset,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.portable_results import (
    PRIMARY,
    verify_result,
)


class TrainingPipeline:
    def __init__(self, dataset, settings, requirements, output):
        self.dataset = Path(dataset).resolve()
        self.settings = settings
        self.requirements = requirements
        self.output = Path(output).resolve()

    def __call__(self):
        from chara import Chara

        self._validate_source()
        cached = self._prepare_request()
        if cached:
            return cached
        self._check_remote()
        reference = Chara.call(self._train, "remote_training")()
        cache_name = Chara.call(lambda: self._export(reference), "export_result")()
        Chara.call(lambda: self._download(cache_name, reference), "download_result")()
        # Cache entries contain paths, not proof that files still exist.
        if not all(
            (self.output / name).is_file()
            for name in (
                *PRIMARY,
                self.settings.model_name + ".onnx",
                "result-manifest.json",
            )
        ):
            self._download(cache_name, reference)
        verify_result(self.output, reference)
        snapshot = read_json(self.output / "data-snapshot.json")
        if (
            snapshot["generation_settings"].get("portable_corpus_id")
            != self.manifest["corpus_id"]
        ):
            raise ValueError("downloaded training result belongs to a different corpus")
        write_json(
            self.output / "complete.json",
            {"request_identity": self.request_identity, "reference": reference},
        )
        return self._result()

    def _validate_source(self):
        from .generation.packaging import package_dataset

        if (self.dataset / "portable-dataset/manifest.json").exists():
            self.source = self.dataset / "portable-dataset"
        elif self.dataset.name == "portable-dataset":
            self.source = self.dataset
        else:
            self.source = Path(package_dataset(self.dataset)["dataset_folder"])
        self.manifest = validate_dataset(self.source, self.requirements)
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
            write_archive,
        )

        self.archive = self.source.parent / "dataset.zip"
        write_archive(self.archive, {name: self.source / name for name in FILES})

    def _prepare_request(self):
        self.request_identity = identity(
            {
                "corpus_id": self.manifest["corpus_id"],
                "settings": self.settings.canonical(),
                "expected": self.requirements,
            }
        )
        path = self.output / "request.json"
        if path.exists():
            self.request = read_json(path)
            if self.request["identity"] != self.request_identity:
                raise ValueError("request changed; choose new output")
        else:
            if any(p.name != ".wakeword.lock" for p in self.output.iterdir()):
                raise ValueError("output is not empty; choose new output")
            self.request = {
                "identity": self.request_identity,
                "training_id": uuid4().hex,
                "task_id": uuid4().hex,
                "export_task_id": uuid4().hex,
            }
            write_json(path, self.request)
        if (self.output / "complete.json").exists():
            if not all(
                (self.output / name).exists()
                for name in ("report.html", "report_ru.html")
            ):
                from brainbox.deciders.voice_analysis.wakeword_training.runtime.reporting import (
                    render_training_report,
                )

                render_training_report(self.output)
            verify_result(
                self.output, read_json(self.output / "complete.json")["reference"]
            )
            return self._result()
        return None

    def _check_remote(self):
        from brainbox.deciders import WakewordTraining
        from chara import Chara

        self.api = Chara.Apis.brainbox_api
        readiness = self.api.execute(WakewordTraining.new_task().readiness())
        if readiness.get("protocol_version") != 1 or not readiness.get("ready"):
            raise RuntimeError(
                "WakewordTraining not ready; run prepare: " + str(readiness)
            )

    def _train(self):
        from brainbox.deciders import WakewordTraining

        from .training.submission import Submission

        previous = self._existing_job(self.request["task_id"])
        if previous is not None and previous.finished and previous.error:
            status = self.api.execute(
                WakewordTraining.new_task().describe(self.request["training_id"])
            )
            if status.get("reference"):
                return status["reference"]
            if not status.get("training_complete"):
                raise RuntimeError(
                    "partial or failed training requires a new output: "
                    + str(previous.error)
                )
            self.request["task_id"] = uuid4().hex
            write_json(self.output / "request.json", self.request)
        dataset_name = "wakeword-dataset." + self.request["task_id"] + ".zip"
        if previous is None or (previous.finished and previous.error):
            self.api.cache.upload(dataset_name, self.archive)
        client = Submission(self.api, self.output)
        task = WakewordTraining.new_task(id=self.request["task_id"]).train(
            self.request["training_id"],
            self.settings.canonical(),
            {**self.requirements, "corpus_id": self.manifest["corpus_id"]},
            dataset_name,
        )
        identity = client.submit(task, self.request["task_id"])
        return client.follow(identity, streamed=True)

    def _existing_job(self, identity):
        try:
            return self.api.jobs.get_job(identity)
        except Exception as error:
            if "Can't find a job with id " + identity not in str(error):
                raise RuntimeError(
                    "transport_unknown: job state unavailable"
                ) from error
            return None

    def _export(self, reference):
        from brainbox.deciders import WakewordTraining

        from .training.submission import Submission

        previous = self._existing_job(self.request["export_task_id"])
        if previous is not None and previous.finished and previous.error:
            self.request["export_task_id"] = uuid4().hex
            write_json(self.output / "request.json", self.request)
        task = WakewordTraining.new_task(id=self.request["export_task_id"]).export(
            reference
        )
        client = Submission(self.api, self.output)
        identity = client.submit(task, self.request["export_task_id"])
        cache_name = client.follow(identity)
        self.request["export_cache_name"] = cache_name
        write_json(self.output / "request.json", self.request)
        return cache_name

    def _download(self, cache_name, reference):
        from .training.results import download

        if not self.api.cache.is_file(cache_name):
            # A cached Chara path may refer to an expired BrainBox cache entry.
            if self.request.get("export_cache_name", cache_name) == cache_name:
                self.request["export_task_id"] = uuid4().hex
                self.request.pop("export_cache_name", None)
                write_json(self.output / "request.json", self.request)
            cache_name = self._export(reference)
        return download(
            self.api, cache_name, self.output, reference, self.settings.model_name
        )

    def _result(self):
        return TrainingResult(
            "complete",
            self.output,
            self.output / (self.settings.model_name + ".onnx"),
            self.output / "report.html",
            self.output / "metrics.json",
            report_ru=self.output / "report_ru.html",
            history=self.output / "history.jsonl",
            scores=self.output / "scores",
            manifest=self.output / "result-manifest.json",
            remote_reference=read_json(self.output / "complete.json")["reference"],
        )


def train_dataset(dataset, settings, expected_dataset, output):
    from chara import Chara

    output = Path(output).resolve()
    with run_lock(output):
        # Use a nested Chara directory, so state/identity survive incomplete phase cleanup.
        pipeline = TrainingPipeline(dataset, settings, expected_dataset, output)
        pipeline._validate_source()
        cached = pipeline._prepare_request()
        if cached:
            return cached
        Chara.start(output / "orchestration")
        return Chara.call(pipeline, "training_pipeline")()
