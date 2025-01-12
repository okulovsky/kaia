from brainbox.framework.containerized_brainbox import ContainerizedBrainboxTestEnvironment
from brainbox.doc import run_all
from unittest import TestCase


class DockerizedBrainBoxDebugTestCase(TestCase):
    def test_dockerized_brainbox_with_debugging(self):
        with ContainerizedBrainboxTestEnvironment() as api:
            run_all(api)




