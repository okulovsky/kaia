from brainbox.deciders.utils.boilerplate import Boilerplate
from unittest import TestCase

class BoilerplateAloneTestCase(TestCase):
    def test_installation(self):
        controller = Boilerplate.Controller()
        controller.uninstall()

        self.assertFalse(controller.is_installed())
        controller.install()
        self.assertTrue(controller.is_installed())

        running = controller.get_running_instances_id_to_parameter()
        self.assertDictEqual({}, running)

        model = 'TestModel'
        instance_id = controller.run(model)
        self.assertTrue(controller.is_reachable())

        running = controller.get_running_instances_id_to_parameter()
        self.assertDictEqual({instance_id:model}, running)

        api = controller.find_api(instance_id)
        result = api.json('argument')
        self.assertDictEqual(
            {'argument': 'argument', 'model': 'TestModel', 'setting': 'default_setting'},
            result
        )

        controller.stop_all()
        self.assertFalse(controller.is_reachable())
        self.assertEqual(0, len(controller.get_running_instances_id_to_parameter()))

