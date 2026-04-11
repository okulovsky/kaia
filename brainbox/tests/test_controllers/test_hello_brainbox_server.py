from brainbox.framework.app.controllers import ControllersStatus, ControllerStatus
from brainbox.framework import BrainBoxApi
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from unittest import TestCase


def _cs(status: ControllersStatus) -> ControllerStatus:
    return next(c for c in status.controllers if c.name == 'HelloBrainBox')


def _first_install_to_check_if_installable(self: TestCase, api: BrainBoxApi):
    api.controllers.uninstall(HelloBrainBox, True)
    status = api.controllers.status()
    self.assertFalse(_cs(status).installed)

    api.controllers.install.execute(HelloBrainBox)

    status = api.controllers.status()
    self.assertTrue(_cs(status).installed)
    self.assertEqual(0, len(_cs(status).instances))



def make_api_test(self: TestCase, api: BrainBoxApi):
    _first_install_to_check_if_installable(self, api)

    api.controllers.uninstall(HelloBrainBox, True)
    status = api.controllers.status()
    self.assertFalse(_cs(status).installed)

    self.assertRaises(Exception, lambda: api.controllers.run(HelloBrainBox, 'must_fail'))

    key = api.controllers.install.start(HelloBrainBox)
    status = api.controllers.status()
    self.assertFalse(_cs(status).installed)
    api.controllers.install.join(key)

    status = api.controllers.status()
    self.assertTrue(_cs(status).installed)
    self.assertEqual(0, len(_cs(status).instances))

    instance_id = api.controllers.run(HelloBrainBox, None)

    brainbox_api = HelloBrainBox.Api('127.0.0.1:20000')
    result = brainbox_api.sum(2, 4)
    self.assertEqual(6, result)

    status = api.controllers.status()
    self.assertEqual(instance_id, _cs(status).instances[0].instance_id)

    api.controllers.stop(HelloBrainBox, instance_id)
    status = api.controllers.status()
    self.assertEqual(0, len(_cs(status).instances))

    api.controllers.self_test.execute(HelloBrainBox)


class HelloBrainBoxWebServerTestCase(TestCase):
    def test_web_server(self):
        with BrainBoxApi.test([HelloBrainBox.Controller()], default_resources_folder=False) as api:
            make_api_test(self, api)
