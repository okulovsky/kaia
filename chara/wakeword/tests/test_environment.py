import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from wakeword.generation import environment as env


class Storage:
    def __init__(self, files):
        self.files = files

    def is_file(self, name):
        return name in self.files

    def read(self, name):
        return self.files[name].encode()

    def list(self, path, **kwargs):
        return [
            p[len(path) + 1 :]
            for p in self.files
            if p.startswith(path + "/") and p.endswith(kwargs["suffix"])
        ]


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.resource_folder = Path(self.temporary.name)
        (self.resource_folder / "manifest.json").write_text("{}")
        for target, kwargs in [
            ("wakeword.generation.dependencies.issues", {"return_value": []}),
            (
                "wakeword.generation.local.resources.ResourceInstaller.load",
                {"return_value": {}},
            ),
            (
                "wakeword.generation.local.resources.ResourceInstaller.prepare",
                {"return_value": {}},
            ),
        ]:
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fixture(self):
        spec = {
            "id": "test.wav",
            "kind": "background_wav",
            "source": "file:///resources/test.wav",
            "revision": "1",
        }
        dict(
            spec,
            sha256="abc",
            artifacts=[{"file": "abc/audio.wav", "sha256": "abc", "size": 1}],
        )
        stores = {
            "ParlerTts": Storage({"installation.yaml": "mini-v1: repo"}),
            "Vosk": Storage({"installation.yaml": "en:\n  url: url"}),
        }
        api = SimpleNamespace(
            controllers=SimpleNamespace(
                status=lambda: SimpleNamespace(
                    controllers=[
                        SimpleNamespace(name=n, installed=True) for n in stores
                    ]
                )
            ),
            resources=lambda n: stores[n],
        )
        return (
            api,
            SimpleNamespace(
                resource_specs=[spec], resource_folder=str(self.resource_folder)
            ),
            stores,
        )

    @patch.object(
        env,
        "requirements",
        return_value={"ParlerTts": ("mini-v1", "repo"), "Vosk": ("en", {"url": "url"})},
    )
    def test_check_reads_only_and_detects_missing_model(self, _):
        api, settings, stores = self.fixture()
        self.assertTrue(env.ready(env.check(api, settings)))
        stores["Vosk"].files["installation.yaml"] = "{}"
        rows = env.check(api, settings)
        self.assertEqual(
            [r.component for r in rows if r.state == "missing"], ["Vosk/en"]
        )

    @patch.object(
        env,
        "requirements",
        return_value={"ParlerTts": ("mini-v1", "repo"), "Vosk": ("en", {"url": "url"})},
    )
    def test_conflicts_and_missing_artifacts_are_blocked(self, _):
        api, settings, stores = self.fixture()
        stores["ParlerTts"].files["installation.yaml"] = "mini-v1: other"

        rows = env.check(api, settings)
        self.assertEqual(
            {r.component for r in rows if r.state == "blocked"}, {"ParlerTts/mini-v1"}
        )

    @patch.object(
        env,
        "requirements",
        return_value={"ParlerTts": ("mini-v1", "repo"), "Vosk": ("en", {"url": "url"})},
    )
    def test_setup_downloads_only_missing_model_without_installing_image(self, _):
        from unittest.mock import Mock

        api, settings, stores = self.fixture()
        stores["Vosk"].files["installation.yaml"] = "{}"
        api.controllers.install = Mock()
        tasks = []

        def execute(task):
            tasks.append(task)
            stores["Vosk"].files["installation.yaml"] = "en:\n  url: url"

        api.execute = execute
        with patch("builtins.print"):
            env.setup(api, settings)
        api.controllers.install.start.assert_not_called()
        self.assertEqual(len(tasks), 1)  # only the missing Vosk model
        self.assertTrue(env.ready(env.check(api, settings)))

    @patch.object(
        env,
        "requirements",
        return_value={"ParlerTts": ("mini-v1", "repo"), "Vosk": ("en", {"url": "url"})},
    )
    def test_setup_stops_before_changes_on_conflict(self, _):
        from unittest.mock import Mock

        api, settings, stores = self.fixture()
        stores["Vosk"].files["installation.yaml"] = "en:\n  url: different"
        api.execute = Mock()
        with patch("builtins.print"), self.assertRaises(RuntimeError):
            env.setup(api, settings)
        api.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
