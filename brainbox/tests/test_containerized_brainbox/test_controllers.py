from brainbox.framework.containerized_brainbox import BrainBoxRunner
from unittest import TestCase, skipIf
from brainbox.tests.test_controllers.test_boilerplate_server import test_api
from brainbox.framework import ControllerApi, Loc
from brainbox.framework import ApiUtils
import os

class ControllersInContainerTestCase(TestCase):
    @skipIf(
        "TOX_ENV_NAME" in os.environ,
        "This test is not suitable for running under tox"
    )
    def test_controllers_in_container(self):
        runner = BrainBoxRunner(Loc.root_folder, 18090)
        runner.get_deployment().stop().remove().build().run()
        try:
            ApiUtils.wait_for_reply('http://127.0.0.1:18090', 5)
            api = ControllerApi('127.0.0.1:18090')
            api.wait(20)
            test_api(self, api)
        finally:
            runner.get_deployment().stop().remove()

