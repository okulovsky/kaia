from typing import Iterable

from kaia.brainbox.core import IInstaller, IApiDecider, BrainBoxTask, BrainBoxTestApi, IntegrationTestResult
from unittest import TestCase

class Test(IApiDecider):
    def __init__(self, parameters: str):
        self.load_parameters = parameters

    def __call__(self, given_parameter):
        return dict(given=given_parameter, load=self.load_parameters, how='call')

    def method(self, given_parameter):
        return dict(given=given_parameter, load=self.load_parameters, how='method')


class TestInstaller(IInstaller):
    def install(self):
        pass

    def uninstall(self, purge: bool = False):
        pass

    def is_installed(self):
        return True

    def warmup(self, parameters: str):
        self.parameters = parameters

    def cooldown(self, parameters: str):
        self.parameters = None

    def create_brainbox_decider_api(self, parameters: str|None) -> IApiDecider:
        return Test(self.parameters)

    def _brainbox_self_test_internal(self, api, tc: TestCase) -> Iterable[IntegrationTestResult]:
        pass

class InstallerAsDeciderTestCase(TestCase):
    def test_installer_as_decider(self):
        services = {'Test': TestInstaller()}
        tasks = [
            BrainBoxTask(decider=Test, arguments=dict(given_parameter='x'), decider_parameters='X'),
            BrainBoxTask(decider=Test.method, arguments=dict(given_parameter='y'), decider_parameters='Y')
        ]
        result, _ = BrainBoxTestApi.execute_serverless(tasks, services)
        self.assertDictEqual(dict(given='x', load='X', how='call'), result[0].result)
        self.assertDictEqual(dict(given='y', load='Y', how='method'), result[1].result)



