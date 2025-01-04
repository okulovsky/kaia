from brainbox.doc import run_all
from unittest import TestCase, skipIf
import os
from brainbox.framework.containerized_brainbox import BrainBoxRunner
from brainbox.framework import Loc, ApiUtils, BrainBoxApi


class ReadmeInContainerTestCase(TestCase):
    @skipIf(
        "TOX_ENV_NAME" in os.environ,
        "This test is not suitable for running under tox"
    )
    def test_controllers_in_container(self):
        runner = BrainBoxRunner(Loc.root_folder, 18090)
        runner.get_deployment().stop().remove().build().run()
        try:
            ApiUtils.wait_for_reply('http://127.0.0.1:18090', 5)
            api = BrainBoxApi('127.0.0.1:18090')
            api.wait(10)
            run_all(api, self)
        finally:
            runner.get_deployment().stop().remove()

