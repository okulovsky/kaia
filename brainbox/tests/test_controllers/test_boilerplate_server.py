from brainbox.framework.controllers import ControllerApi
from brainbox.deciders.utils.boilerplate import Boilerplate
from unittest import TestCase

def test_api(self: TestCase, api: ControllerApi):
    api.uninstall(Boilerplate)
    status = api.status()
    self.assertIsNone(status.currently_installing_container)
    self.assertEqual(1, len(status.containers))
    self.assertFalse(status.containers[0].installation_status.installed)

    self.assertRaises(Exception, lambda: api.run(Boilerplate, 'must_fail'))

    api.install(Boilerplate, False)
    status = api.status()
    self.assertFalse(status.containers[0].installation_status.installed)
    self.assertEqual('Boilerplate', status.currently_installing_container)
    api.join_installation()

    status = api.status()
    self.assertTrue(status.containers[0].installation_status.installed)
    self.assertEqual(0, len(status.containers[0].instances))
    self.assertIsNone(status.currently_installing_container)

    self.assertRaises(Exception, lambda: api.run(Boilerplate))

    instance_id = api.run(Boilerplate, 'test')

    boilerplate_api = Boilerplate('127.0.0.1:20000')
    result = boilerplate_api.json('test')

    self.assertDictEqual(
        {'argument': 'test', 'model': 'test', 'setting': 'default_setting'},
        result
    )

    status = api.status()
    self.assertEqual(instance_id, status.containers[0].instances[0].instance_id)

    api.stop(Boilerplate, instance_id)
    status = api.status()
    self.assertEquals(0, len(status.containers[0].instances))


class BoilerplateWebServerTestCase(TestCase):
    def test_web_server(self):
        with ControllerApi.Test([Boilerplate.Controller()]) as api:
            test_api(self, api)









