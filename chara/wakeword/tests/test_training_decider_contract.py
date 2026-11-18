import tempfile
import unittest
from pathlib import Path

from training_fixtures import dataset_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    write_json,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.portable_results import (
    verify_result,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.server import (
    ServerTraining,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
    TrainingSettings,
)
from chara.wakeword.generation.packaging import package_dataset


class ServerNativeTests(unittest.TestCase):
    def test_native_training_and_portable_result(self):
        import shutil

        from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
            extract_archive,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.portable_results import (
            PRIMARY,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.reporting import (
            render_training_report,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = dataset_fixture(root / "source")
            path = source / "dataset/manifest.json"
            m = read_json(path)
            m["lineage"] = [
                {
                    "lineage_id": f"{label}-{split}-{i}",
                    "sample_id": f"{label}-{split}-{i}",
                    "class_label": label,
                    "split": split,
                }
                for label in ("positive", "negative")
                for split in ("train", "test")
                for i in range(3)
            ]
            write_json(path, m)
            package = package_dataset(source)
            portable = Path(package["dataset_folder"])
            manifest = read_json(portable / "manifest.json")
            resources = root / "server"
            background = resources / "background"
            background.mkdir(parents=True)
            item = m["resources"]["resources"][0]
            for artifact in item["artifacts"]:
                shutil.copyfile(
                    source / "resources" / artifact["file"],
                    background / artifact["file"],
                )
            write_json(
                background / "manifest.json",
                {"feature_space": manifest["feature_space"], "resource": item},
            )
            server = ServerTraining(resources)
            parameters = TrainingSettings(stage_steps=[1, 1, 1]).canonical()
            expected = {
                "target_variants": ["fixture"],
                "minimum_positive_counts": {"train": 3, "validation": 3},
            }
            result = server.train("native", parameters, expected, portable)
            output = resources / "training/native/artifacts"
            self.assertTrue((output / "wakeword.onnx").exists())
            host = root / "host"
            host.mkdir()
            from chara.wakeword.training_pipeline import (
                TrainingPipeline,
                train_dataset,
            )

            settings = TrainingSettings(stage_steps=[1, 1, 1])
            pipeline = TrainingPipeline(portable, settings, expected, host)
            pipeline._validate_source()
            pipeline._prepare_request()
            extract_archive(
                output / "result.zip",
                host,
                {*PRIMARY, "wakeword.onnx", "result-manifest.json"},
            )
            verify_result(host, result)
            self.assertFalse(list(host.glob("*.pt")))
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
                sha256,
            )

            primary = [
                "wakeword.onnx",
                "history.jsonl",
                "scores/positive_validation.npy",
                "result-manifest.json",
            ]
            before = {name: sha256(host / name) for name in primary}
            (host / "report.html").unlink()
            render_training_report(host)
            self.assertEqual(before, {name: sha256(host / name) for name in primary})
            verify_result(host, result)
            self.assertTrue((host / "report_ru.html").exists())
            write_json(
                host / "complete.json",
                {"request_identity": pipeline.request_identity, "reference": result},
            )
            from unittest.mock import patch

            with patch.object(
                TrainingPipeline,
                "_check_remote",
                side_effect=AssertionError("must stay offline"),
            ):
                self.assertEqual(
                    train_dataset(portable, settings, expected, host).status, "complete"
                )
            history_hash = sha256(output / "history.jsonl")
            self.assertEqual(
                server.train("native", parameters, expected, portable), result
            )
            self.assertEqual(sha256(output / "history.jsonl"), history_hash)
            with self.assertRaisesRegex(ValueError, "immutable"):
                server.train("native", {**parameters, "seed": 41}, expected, portable)


class TrainingTransportTests(unittest.TestCase):
    def test_interface_uses_websocket_training_and_filelike_export(self):
        from brainbox.deciders.voice_analysis.wakeword_training.app.interface import (
            IWakewordTraining,
        )
        from foundation_kaia.marshalling.protocol.model.service_model import (
            ServiceModel,
        )

        endpoints = {
            endpoint.signature.name: endpoint
            for endpoint in ServiceModel.parse(IWakewordTraining).endpoints
        }
        self.assertEqual(set(endpoints), {"readiness", "describe", "train", "export"})
        self.assertEqual(endpoints["train"].protocol.type.name, "WebSockets")
        self.assertEqual(endpoints["export"].result.type.name, "BinaryFile")

    def test_filelike_receiving_extracts_only_into_server_run(self):
        from types import SimpleNamespace

        from brainbox.deciders.voice_analysis.wakeword_training.app.service import (
            WakewordTrainingService,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
            FILES,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.self_test import (
            create_self_test_dataset,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = create_self_test_dataset(root / "host/dataset", {"fixture": True})
            service = WakewordTrainingService(
                SimpleNamespace(resources_folder=root / "server")
            )
            extracted = service._receive_dataset("transport", archive)
            self.assertTrue(
                extracted.is_relative_to(root / "server/training/transport")
            )
            self.assertEqual({path.name for path in extracted.iterdir()}, FILES)
