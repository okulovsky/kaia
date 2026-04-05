import tempfile
from pathlib import Path
from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from brainbox.framework.app.controllers import InstallationReport
from brainbox.framework.app.controllers.api import ControllersApi
from brainbox.framework.app.controllers.dto import ControllersStatus
from foundation_kaia.misc.loc import Locator


def _bps(status: ControllersStatus):
    return next(c for c in status.controllers if c.name == 'HelloBrainBox')


def make_api_test(self: TestCase, api: ControllersApi, locator: Locator):
    api.uninstall(HelloBrainBox, True)
    status = api.status()
    self.assertIsNone(status.currently_installing)
    self.assertFalse(_bps(status).installed)

    api.install(HelloBrainBox, True)
    status = api.status()
    self.assertTrue(_bps(status).installed)
    self.assertEqual(0, len(_bps(status).instances))
    self.assertIsNone(status.currently_installing)

    api.uninstall(HelloBrainBox, True)
    self.assertRaises(Exception, lambda: api.run(HelloBrainBox, 'must_fail'))

    api.install(HelloBrainBox, False)
    status = api.status()
    self.assertFalse(_bps(status).installed)
    self.assertEqual('HelloBrainBox', status.currently_installing)

    report = api.installation_report()
    self.assertIsInstance(report, InstallationReport)

    api.join_installation()

    status = api.status()
    self.assertTrue(_bps(status).installed)
    self.assertEqual(0, len(_bps(status).instances))
    self.assertIsNone(status.currently_installing)

    instance_id = api.run(HelloBrainBox, None)

    brainbox_api = HelloBrainBox.Api('127.0.0.1:20000')
    result = brainbox_api.sum(2, 4)
    self.assertEqual(6, result)

    status = api.status()
    self.assertEqual(instance_id, _bps(status).instances[0].instance_id)

    api.stop(HelloBrainBox, instance_id)
    status = api.status()
    self.assertEqual(0, len(_bps(status).instances))

    controller = HelloBrainBox.Controller()
    report_path = locator.self_test_path / controller.get_name()

    api.self_test(HelloBrainBox)
    self.assertTrue(report_path.is_file())

    api.delete_self_test(HelloBrainBox)
    self.assertFalse(report_path.is_file())


class HelloBrainBoxNewAppTestCase(TestCase):
    def test_hello_brainbox_controllers(self):
        with tempfile.TemporaryDirectory() as tmp:
            locator = Locator(Path(tmp))
            with ControllersApi.test([HelloBrainBox.Controller()], custom_folder=Path(tmp)) as api:
                make_api_test(self, api, locator)
