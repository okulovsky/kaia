from unittest import TestCase
from brainbox.deciders import BoilerplateOnDemand, FakeFile
from brainbox.framework import BrainBox

class BoilerplateServerTestCase(TestCase):
    def test_boilerplate(self):
        with BrainBox.Api.Test() as api:
            api.controller_api.uninstall(BoilerplateOnDemand, True)
            api.controller_api.install(BoilerplateOnDemand)
            result = api.controller_api.self_test(BoilerplateOnDemand)

            api.execute(BrainBox.Task.call(BoilerplateOnDemand).execute('test'))
            api.execute(BrainBox.Task.call(FakeFile)())