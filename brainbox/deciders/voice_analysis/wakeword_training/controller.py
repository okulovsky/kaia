import shutil
from pathlib import Path

from foundation_kaia.brainbox_utils import Installer

from ....framework import (
    BrainboxImageBuilder,
    DockerMarshallingController,
    RunConfiguration,
)
from .app.installer import WakewordTrainingInstaller
from .settings import WakewordTrainingSettings


class WakewordTrainingController(DockerMarshallingController[WakewordTrainingSettings]):
    def get_image_builder(self):
        from . import runtime as core

        root = Path(__file__).parent
        target = root / "app/wakeword_core"
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError("invalid staging path")
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(
            Path(core.__file__).parent,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        shutil.copyfile(
            root / "files/resource-profile.json", root / "app/resource-profile.json"
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
            sha256,
            write_json,
        )

        write_json(
            target / "source-identity.json",
            {
                str(path.relative_to(target)).replace("\\", "/"): sha256(path)
                for path in sorted(target.rglob("*.py"))
            },
        )
        return BrainboxImageBuilder(
            root,
            "3.11.11",
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_installer(self) -> Installer:
        return WakewordTrainingInstaller(self.resource_folder())

    def get_service_run_configuration(self, port, parameter):
        return RunConfiguration(publish_ports={port: 8080})

    def get_loading_time_in_seconds(self):
        return 60

    def create_api(self, base_url):
        from .api import WakewordTrainingApi

        return WakewordTrainingApi(base_url)

    def custom_self_test(self, api, tc):
        import json
        import tempfile
        from uuid import uuid4

        from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
            extract_archive,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.portable_results import (
            PRIMARY,
            verify_result,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.self_test import (
            create_self_test_dataset,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
            TrainingSettings,
        )

        from .api import WakewordTraining

        readiness = api.execute(WakewordTraining.new_task().readiness())
        tc.assertTrue(readiness["ready"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dataset = create_self_test_dataset(
                root / "dataset", readiness["profile"]["feature_space"]
            )
            dataset_name = "wakeword-self-test." + uuid4().hex + ".zip"
            api.cache.upload(dataset_name, dataset)
            task = WakewordTraining.new_task().train(
                "self-test-" + uuid4().hex,
                TrainingSettings(stage_steps=[1, 1, 1]).canonical(),
                {
                    "target_variants": ["synthetic-self-test"],
                    "minimum_positive_counts": {"train": 3, "validation": 3},
                    "resource_profile": readiness["profile"]["profile_id"],
                },
                dataset_name,
            )
            stream = api.execute(task)
            events = [
                json.loads(line)
                for line in api.cache.read(stream).decode("utf-8").splitlines()
                if line.strip()
            ]
            reference = next(
                event["result"] for event in reversed(events) if event.get("result")
            )
            cache_name = api.execute(WakewordTraining.new_task().export(reference))
            archive = root / "result.zip"
            with archive.open("wb") as output:
                for chunk in api.cache.open(cache_name):
                    output.write(chunk)
            extracted = extract_archive(
                archive,
                root / "result",
                {*PRIMARY, "wakeword.onnx", "result-manifest.json"},
            )
            verify_result(extracted, reference)
            tc.assertFalse(list(extracted.rglob("*.pt")))
            tc.assertTrue((extracted / "report_ru.html").is_file())
