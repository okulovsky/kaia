from brainbox.framework.app.controllers import ControllersApi, ControllersStatus, ControllerStatus
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from unittest import TestCase


def _cs(status: ControllersStatus) -> ControllerStatus:
    return next(c for c in status.controllers if c.name == 'HelloBrainBox')


def _first_install_to_check_if_installable(self: TestCase, api: ControllersApi):
    api.uninstall(HelloBrainBox, True)
    status = api.status()
    self.assertIsNone(status.currently_installing)
    self.assertFalse(_cs(status).installed)

    api.install(HelloBrainBox, True)

    status = api.status()
    self.assertTrue(_cs(status).installed)
    self.assertEqual(0, len(_cs(status).instances))
    self.assertIsNone(status.currently_installing)


def make_api_test(self: TestCase, api: ControllersApi):
    _first_install_to_check_if_installable(self, api)

    api.uninstall(HelloBrainBox, True)
    status = api.status()
    self.assertIsNone(status.currently_installing)
    self.assertFalse(_cs(status).installed)

    self.assertRaises(Exception, lambda: api.run(HelloBrainBox, 'must_fail'))

    api.install(HelloBrainBox, False)
    status = api.status()
    self.assertFalse(_cs(status).installed)
    self.assertEqual('HelloBrainBox', status.currently_installing)
    api.join_installation()

    status = api.status()
    self.assertTrue(_cs(status).installed)
    self.assertEqual(0, len(_cs(status).instances))
    self.assertIsNone(status.currently_installing)

    instance_id = api.run(HelloBrainBox, None)

    brainbox_api = HelloBrainBox.Api('127.0.0.1:20000')
    result = brainbox_api.sum(2, 4)
    self.assertEqual(6, result)

    status = api.status()
    self.assertEqual(instance_id, _cs(status).instances[0].instance_id)

    api.stop(HelloBrainBox, instance_id)
    status = api.status()
    self.assertEqual(0, len(_cs(status).instances))

    api.self_test(HelloBrainBox)


class HelloBrainBoxWebServerTestCase(TestCase):
    def test_web_server(self):
        with ControllersApi.test([HelloBrainBox.Controller()]) as api:
            make_api_test(self, api)
