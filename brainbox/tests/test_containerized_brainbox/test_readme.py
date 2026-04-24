from brainbox.framework.container import ContainerizedBrainboxTestEnvironment
from foundation_kaia.releasing.mddoc import run_doc_files
from unittest import TestCase, skipIf
import os
import platform
from pathlib import Path


class DockerizedBrainBoxDebugTestCase(TestCase):
    @skipIf(
        platform.system() == "Windows" or "TOX_ENV_DIR" in os.environ,
        "Test not supported on Windows or in Tox"
    )
    def test_dockerized_brainbox_with_debugging(self):
        with ContainerizedBrainboxTestEnvironment() as api:
            run_doc_files(self, Path(__file__).parent.parent.parent / "doc")




