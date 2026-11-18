"""Host training orchestration must not import local model runtimes."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


class ImportBoundaryTests(unittest.TestCase):
    def test_lightweight_contract_imports(self):
        root = Path(__file__).resolve().parents[3]
        code = """
import importlib.abc, sys
class BlockModels(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'numpy', 'onnx', 'onnxruntime', 'matplotlib', 'openwakeword'}:
            raise RuntimeError('unexpected host ML import: ' + fullname)
sys.meta_path.insert(0, BlockModels())
sys.path.insert(0, "brainbox/deciders/voice_analysis/wakeword_training")
from runtime.settings import TrainingSettings
from runtime.manifests import validate_dataset
from runtime.archives import extract_archive
assert TrainingSettings().device == 'cpu'
"""
        env = {**os.environ, "PYTHONPATH": str(root)}
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_chara_does_not_load_model_runtimes(self):
        root = Path(__file__).resolve().parents[3]
        code = """
import importlib.abc, sys
class BlockModels(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'onnx', 'onnxruntime', 'openwakeword'}:
            raise RuntimeError('unexpected model runtime: ' + fullname)
sys.meta_path.insert(0, BlockModels())
from chara import Chara
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_entrypoints_help(self):
        root = Path(__file__).resolve().parents[3]
        for command in ("generate", "train", "prepare", "report"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "chara.wakeword.scripts." + command,
                        "--help",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
