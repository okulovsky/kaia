from brainbox.framework.containerized_brainbox import BrainBoxRunner
from unittest import TestCase, skipIf
from brainbox.framework import Loc, ApiUtils, BrainBoxApi, BrainBoxTask
from yo_fluq import Query
from brainbox.deciders import HelloBrainBox
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
            api = BrainBoxApi('127.0.0.1:18090')
            api.wait(10)
            status = api.controller_api.status()
            if not Query.en(status.containers).where(lambda z: z.name=='HelloBrainBox').single().installation_status.installed:
                api.controller_api.install(HelloBrainBox)
            result = api.execute(BrainBoxTask.call(HelloBrainBox, 'TestParameter').json('TestArgument'))
            self.assertIsInstance(result, dict)
        finally:
            runner.get_deployment().stop().remove()
