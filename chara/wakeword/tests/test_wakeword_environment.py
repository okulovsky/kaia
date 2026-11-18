"""Preparation remains explicit and checks are read only."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from chara.wakeword.environment import prepare_training


class EnvironmentTests(unittest.TestCase):
    def test_check_only_does_not_install(self):
        api = SimpleNamespace(controllers=Mock(), execute=Mock())
        api.controllers.status.return_value.controllers = [
            SimpleNamespace(name="WakewordTraining", installed=False)
        ]
        self.assertFalse(prepare_training(api, check_only=True)["ready"])
        api.execute.assert_not_called()
        api.controllers.install.start.assert_not_called()

    def test_unregistered_server_has_update_instruction(self):
        api = SimpleNamespace(controllers=Mock())
        api.controllers.status.return_value.controllers = []
        with self.assertRaisesRegex(RuntimeError, "update server code"):
            prepare_training(api)
        api.controllers.install.start.assert_not_called()

    def test_explicit_install_repairs_despite_old_marker(self):
        from brainbox.deciders.voice_analysis.wakeword_training.app.installer import (
            WakewordTrainingInstaller,
        )

        with tempfile.TemporaryDirectory() as folder:
            installer = WakewordTrainingInstaller(folder)
            installer.installation_file.touch()
            with (
                patch.object(installer, "_execute_installation") as install,
                patch.object(installer, "readiness", return_value={"ready": True}),
            ):
                installer.install_service()
                install.assert_called_once()
            self.assertTrue(Path(folder, "installation.yaml").exists())
