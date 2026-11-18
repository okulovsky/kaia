import tempfile
import unittest
from pathlib import Path

from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
    extract_archive,
    write_archive,
)


class PortableArchiveTests(unittest.TestCase):
    def test_deterministic_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "a"
            source.write_bytes(b"payload")
            write_archive(root / "one.zip", {"a": source})
            write_archive(root / "two.zip", {"a": source})
            self.assertEqual(
                (root / "one.zip").read_bytes(), (root / "two.zip").read_bytes()
            )
            extract_archive(root / "one.zip", root / "out", {"a"})
            self.assertEqual((root / "out/a").read_bytes(), b"payload")

    def test_reject_paths(self):
        import zipfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with zipfile.ZipFile(root / "bad.zip", "w") as archive:
                archive.writestr("../outside", b"bad")
            with self.assertRaises(ValueError):
                extract_archive(root / "bad.zip", root / "out", {"a"})


class PortableDatasetTests(unittest.TestCase):
    def test_requirements_are_independent_and_count_originals(self):
        from remote_training_fixtures import portable_fixture

        from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
            validate_dataset,
        )

        with tempfile.TemporaryDirectory() as temp:
            folder = portable_fixture(Path(temp) / "source")
            for expected in [
                {
                    "target_variants": ["wrong"],
                    "minimum_positive_counts": {"train": 3, "validation": 3},
                },
                {
                    "target_variants": ["fixture"],
                    "minimum_positive_counts": {"train": 4, "validation": 3},
                },
            ]:
                with self.assertRaises(ValueError):
                    validate_dataset(folder, expected)

    def test_nonfinite_header_and_lineage_are_rejected(self):
        import numpy as np
        from remote_training_fixtures import portable_fixture

        from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
            read_json,
            sha256,
            write_json,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
            identity,
            validate_dataset,
        )

        for change in ("nan", "inf", "dtype", "shape", "hash", "overlap", "review"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                folder = portable_fixture(Path(temp) / "source")
                path = folder / "manifest.json"
                manifest = read_json(path)
                if change == "overlap":
                    manifest["lineage"][3]["lineage_id"] = manifest["lineage"][0][
                        "lineage_id"
                    ]
                elif change == "review":
                    manifest["lineage"][0]["review"] = True
                else:
                    part = manifest["parts"]["positive_features_train"]
                    array_path = folder / part["file"]
                    data = np.load(array_path)
                    if change in ("nan", "inf"):
                        data.flat[0] = np.nan if change == "nan" else np.inf
                    elif change == "shape":
                        data = data.reshape(-1, 96)
                    else:
                        data = data.astype(np.float64)
                    np.save(array_path, data)
                    if change != "hash":
                        part["sha256"] = sha256(array_path)
                manifest["corpus_id"] = identity(
                    {
                        key: value
                        for key, value in manifest.items()
                        if key != "corpus_id"
                    }
                )
                write_json(path, manifest)
                with self.assertRaises(ValueError):
                    validate_dataset(folder)

    def test_archive_budget_and_case_collision(self):
        import zipfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with zipfile.ZipFile(root / "bad.zip", "w") as archive:
                archive.writestr("a", b"12345678")
                archive.writestr("A", b"12345678")
            with self.assertRaises(ValueError):
                extract_archive(root / "bad.zip", root / "case", {"a", "A"})
            with self.assertRaises(ValueError):
                extract_archive(root / "bad.zip", root / "budget", {"a", "A"}, budget=4)

    def test_big_endian_float32_is_scanned_correctly(self):
        import numpy as np
        from remote_training_fixtures import portable_fixture

        from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
            read_json,
            sha256,
            write_json,
        )
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
            identity,
            validate_dataset,
        )

        with tempfile.TemporaryDirectory() as temp:
            folder = portable_fixture(Path(temp) / "source")
            manifest = read_json(folder / "manifest.json")
            part = manifest["parts"]["positive_features_train"]
            path = folder / part["file"]
            np.save(path, np.load(path).astype(">f4"))
            part["sha256"] = sha256(path)
            manifest["corpus_id"] = identity(
                {key: value for key, value in manifest.items() if key != "corpus_id"}
            )
            write_json(folder / "manifest.json", manifest)
            self.assertEqual(
                validate_dataset(folder)["corpus_id"], manifest["corpus_id"]
            )

    def test_zip_link_is_rejected(self):
        import stat
        import zipfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            info = zipfile.ZipInfo("a")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(root / "link.zip", "w") as archive:
                archive.writestr(info, "outside")
            with self.assertRaisesRegex(ValueError, "unsupported"):
                extract_archive(root / "link.zip", root / "out", {"a"})
