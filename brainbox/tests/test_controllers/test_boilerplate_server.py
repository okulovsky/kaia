from brainbox.framework.controllers import ControllerApi, ControllerServiceStatus
from brainbox.deciders.utils.hello_world import HelloBrainBox
from unittest import TestCase
from yo_fluq import Query


def _bps(status: ControllerServiceStatus):
    return Query.en(status.containers).where(lambda z: z.name == 'HelloBrainBox').single()


def _first_install_to_check_if_installable(self: TestCase, api:ControllerApi):
    api.uninstall(HelloBrainBox, True)
    status = api.status()
    self.assertIsNone(status.currently_installing_container)
    self.assertFalse(_bps(status).installation_status.installed)

    api.install(HelloBrainBox, True)

    status = api.status()
    self.assertTrue(_bps(status).installation_status.installed)
    self.assertEqual(0, len(_bps(status).instances))
    self.assertIsNone(status.currently_installing_container)

def test_api(self: TestCase, api: ControllerApi):
    _first_install_to_check_if_installable(self, api)

    api.uninstall(HelloBrainBox, True)
    status = api.status()
    self.assertIsNone(status.currently_installing_container)
    self.assertFalse(_bps(status).installation_status.installed)

    self.assertRaises(Exception, lambda: api.run(HelloBrainBox, 'must_fail'))

    api.install(HelloBrainBox, False)
    status = api.status()
    self.assertFalse(_bps(status).installation_status.installed)
    self.assertEqual('HelloBrainBox', status.currently_installing_container)
    api.join_installation()

    status = api.status()
    self.assertTrue(_bps(status).installation_status.installed)
    self.assertEqual(0, len(_bps(status).instances))
    self.assertIsNone(status.currently_installing_container)

    instance_id = api.run(HelloBrainBox, 'test')

    boilerplate_api = HelloBrainBox('127.0.0.1:20000')
    result = boilerplate_api.json('test')

    self.assertDictEqual(
        {'argument': 'test', 'model': 'test', 'setting': 'default_setting'},
        result
    )

    status = api.status()
    self.assertEqual(instance_id, _bps(status).instances[0].instance_id)

    api.stop(HelloBrainBox, instance_id)
    status = api.status()
    self.assertEqual(0, len(_bps(status).instances))


class HelloBrainBoxWebServerTestCase(TestCase):
    def test_web_server(self):
        with ControllerApi.Test([HelloBrainBox.Controller()]) as api:
            test_api(self, api)









