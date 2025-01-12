from unittest import TestCase
from brainbox.deciders import BoilerplateServer
from brainbox.framework import ControllerApi

class BoilerplateServerTestCase(TestCase):
    def test_boilerplate(self):
        with ControllerApi.Test([BoilerplateServer.Controller()]) as api:
            api.uninstall(BoilerplateServer, True)
            api.install(BoilerplateServer)
            result = api.self_test(BoilerplateServer)
            print(result)