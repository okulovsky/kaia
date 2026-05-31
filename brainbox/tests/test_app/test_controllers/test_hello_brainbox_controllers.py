import tempfile
from pathlib import Path
from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from brainbox.framework.app import BrainBoxApi
from brainbox.framework.app.controllers.dto import ControllersStatus



def _bps(status: ControllersStatus):
    return next(c for c in status.controllers if c.name == 'HelloBrainBox')


def make_api_test(self: TestCase, api: BrainBoxApi):
    api.controllers.uninstall(HelloBrainBox, True)
    status = api.controllers.status()
    self.assertFalse(_bps(status).installed)

    api.controllers.install.execute(HelloBrainBox)
    status = api.controllers.status()
    self.assertTrue(_bps(status).installed)
    self.assertEqual(0, len(_bps(status).instances))


    api.controllers.uninstall(HelloBrainBox, True)
    self.assertRaises(Exception, lambda: api.controllers.run(HelloBrainBox, 'must_fail'))

    key = api.controllers.install.start(HelloBrainBox)
    status = api.controllers.status()
    self.assertFalse(_bps(status).installed)


    report = api.controllers.install.html_report(key)
    self.assertIsInstance(report, str)

    api.controllers.install.join(key)

    status = api.controllers.status()
    self.assertTrue(_bps(status).installed)
    self.assertEqual(0, len(_bps(status).instances))


    instance_id = api.controllers.run(HelloBrainBox, None)

    brainbox_api = HelloBrainBox.Api('http://127.0.0.1:20000')
    result = brainbox_api.sum(2, 4)
    self.assertEqual(6, result)

    status = api.controllers.status()
    self.assertEqual(instance_id, _bps(status).instances[0].instance_id)

    api.controllers.stop(HelloBrainBox, instance_id)
    status = api.controllers.status()
    self.assertEqual(0, len(_bps(status).instances))

    controller = HelloBrainBox.Controller()
    report_path = api.debug_locations.self_test_folder / controller.get_name()

    api.controllers.self_test.execute(HelloBrainBox)
    self.assertTrue(report_path.is_file())

    api.controllers.delete_self_test(HelloBrainBox)
    self.assertFalse(report_path.is_file())


class HelloBrainBoxNewAppTestCase(TestCase):
    def test_hello_brainbox_controllers(self):
        with BrainBoxApi.test(
            [HelloBrainBox.Controller()],
            default_resources_folder=False,
        ) as api:
            make_api_test(self, api)
