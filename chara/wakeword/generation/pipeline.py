import shutil
from dataclasses import asdict
from pathlib import Path

from chara import Chara, logger

from .dto import RunResult
from .io import read_json, write_json
from .local.execution import call_local
from .negatives.pipeline import NegativeCollection
from .positives.pipeline import PositiveCollection
from .progress import IncompleteGeneration
from .reporting import write_report
from .resources import prepare_resources, read_voice_models
from .review import save_review
from .run_state import check_settings, run_lock
from .settings import GROUPS
from .validation import FEATURES, check_completed, publish_manifest


class WakewordPipeline:
    def __init__(self, settings, resources=None):
        self.settings = settings
        self.resources = resources

    def _normalize(self, cases):
        from .local.normalization import normalize

        destination = Chara.current.folder / "normalized"
        destination.mkdir(exist_ok=True)
        for case in cases:
            try:
                case.normalized_audio = normalize(
                    case.crop_audio, destination / (case.sample_id + ".wav")
                )
            except (ValueError, RuntimeError) as error:
                case.error = str(error)
                case.error_stage = "normalize"
                case.reason_code = "invalid_audio"
        return cases

    def _features(self, cases, resources):
        from .local.features import compute
        from .local.resources import ResourceInstaller

        folder = Chara.current.folder
        samples = [
            {
                "sample_id": c.sample_id,
                "lineage_id": c.lineage_id,
                "class_label": c.class_label,
                "split": c.split,
                "file": str(Path(c.normalized_audio).resolve()),
            }
            for c in cases
        ]
        root = self._run_root
        paths = ResourceInstaller(self.settings.resource_folder).paths(resources)
        compute(root, folder, {"samples": samples}, self.settings.canonical(), paths)
        return folder

    def __call__(self):
        settings = self.settings.validate()
        root = Chara.current.folder
        self._run_root = root
        (root / "review").mkdir(exist_ok=True)
        resources = self.resources or Chara.call(prepare_resources)(settings)
        write_json(root / "resources.json", resources)
        cases = self._collect_audio(resources, root)
        features = Chara.call(call_local, "features")(self._features, cases, resources)
        return self._publish_dataset(cases, features, resources, root)

    def _collect_audio(self, resources, root):
        groups = {}
        excluded = set()
        version = 0
        while True:
            for group in GROUPS:
                if group in groups and all(c.error is None for c in groups[group]):
                    continue
                self._collect_group(group, groups, resources, root, excluded, version)
            failed = self._normalize_and_review(groups, root, excluded, version)
            if not failed:
                break
            version += 1
        return [c for group in GROUPS for c in groups[group]]

    def _collect_group(self, group, groups, resources, root, excluded, version):
        settings = self.settings
        collector = (
            PositiveCollection(settings, root, excluded)
            if group.startswith("positive")
            else NegativeCollection(settings, resources, root, excluded)
        )
        result = Chara.call(collector, f"{group}_generation_{version:04d}")(group)
        previous = {
            c.sample_id: c
            for c in groups.get(group, [])
            if c.error is None and c.normalized_audio is not None
        }
        groups[group] = [previous.get(c.sample_id, c) for c in result.successes]

    def _normalize_and_review(self, groups, root, excluded, version):
        pending = [
            c for cases in groups.values() for c in cases if c.normalized_audio is None
        ]
        normalized = Chara.call(self._normalize, f"normalize_{version:04d}")(pending)
        by_id = {c.sample_id: c for c in normalized}
        failed = []
        for group, cases in groups.items():
            groups[group] = [by_id.get(c.sample_id, c) for c in cases]
            for case in groups[group]:
                if case.error:
                    excluded.add(case.sample_id)
                    save_review(root, case)
                    failed.append(case)
        return failed

    def _publish_dataset(self, cases, features, resources, root):
        settings = self.settings
        dataset = root / "dataset"
        dataset.mkdir(exist_ok=True)
        for name in FEATURES:
            target = dataset / (name + ".npy")
            temporary = target.with_suffix(".npy.partial")
            shutil.copyfile(features / (name + ".npy"), temporary)
            temporary.replace(target)
        lineage = [
            {
                "sample_id": c.sample_id,
                "lineage_id": c.lineage_id,
                "class_label": c.class_label,
                "split": c.split,
            }
            for c in cases
        ]
        artifacts = publish_manifest(dataset, settings.canonical(), resources, lineage)
        progress = {
            group: read_json(root / "generation_state" / group / "progress.json")
            for group in GROUPS
        }
        result = RunResult(
            "complete",
            settings.canonical(),
            resources,
            progress,
            artifacts,
            str(root / "review"),
            str(root / "report.json"),
        )
        write_report(root, asdict(result))
        return result


def _validate_cached_inputs(settings, output, cached):
    if (output / "dataset/manifest.json").exists():
        manifest = check_completed(output / "dataset")
        if manifest["settings"] != settings.canonical():
            raise ValueError(
                "dataset configuration mismatch; choose a new output folder"
            )
    elif cached:
        raise ValueError("cached run has no completed dataset manifest")
    elif (output / "resources.json").exists():
        previous = read_json(output / "resources.json")
        from .local.resources import ResourceInstaller

        current = ResourceInstaller(settings.resource_folder).load(
            settings.resource_specs
        )
        current["voice_models"] = read_voice_models(settings)
        if previous != current:
            raise ValueError(
                "local resources, dependencies or voice models changed; choose a new output folder"
            )


def run(settings, output):
    output = Path(output).resolve()
    settings.validate()
    with run_lock(output):
        check_settings(output, settings)
        cached = Chara.from_folder(output).has_result
        try:
            _validate_cached_inputs(settings, output, cached)
            Chara.start(output)
            result = Chara.call(WakewordPipeline(settings))()
            if cached:
                write_report(output, asdict(result))
            return result
        except Exception as error:
            try:
                write_report(
                    output,
                    {
                        "status": "incomplete"
                        if isinstance(error, IncompleteGeneration)
                        else "failed",
                        "error": str(error),
                        "settings": settings.canonical(),
                        "review_path": str(output / "review"),
                    },
                )
            except Exception as report_error:  # noqa: BLE001 - Reporting must not hide the original failure.
                logger.error(report_error)
            raise
