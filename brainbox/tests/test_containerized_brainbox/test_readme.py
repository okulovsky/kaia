from brainbox.framework.containerized_brainbox import ContainerizedBrainboxTestEnvironment
from brainbox.doc import run_all
from unittest import TestCase, skipIf
import os
import platform


class DockerizedBrainBoxDebugTestCase(TestCase):
    @skipIf(
        platform.system() == "Windows" or "TOX_ENV_DIR" in os.environ,
        "Test not supported on Windows or in Tox"
    )
    def test_dockerized_brainbox_with_debugging(self):
        with ContainerizedBrainboxTestEnvironment() as api:
            run_all(api)




