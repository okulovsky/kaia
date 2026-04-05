from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from unittest import TestCase
import json


class HelloBrainBoxAloneTestCase(TestCase):
    def test_installation(self):
        controller = HelloBrainBox.Controller()
        controller.uninstall()

        self.assertFalse(controller.is_installed())
        controller.install()
        self.assertTrue(controller.is_installed())

        running = controller.get_running_instances_id_to_parameter()
        self.assertDictEqual({}, running)

        instance_id = controller.run(None)
        self.assertTrue(controller.is_reachable())

        running = controller.get_running_instances_id_to_parameter()
        self.assertDictEqual({instance_id: None}, running)

        api = controller.find_api(instance_id)

        result = api.sum(2, 4)
        self.assertEqual(6, result)

        filename = api.voiceover('hello', 'google')
        with open(api.cache_folder / filename, 'rb') as f:
            content = json.loads(f.read())
        self.assertEqual('hello', content['text'])
        self.assertEqual('[LOADED] /resources/models/google', content['model'])

        result = api.voice_embedding(b'12112')
        self.assertEqual([0,3,2,0,0,0,0,0,0,0], result)

        controller.stop_all()
        self.assertFalse(controller.is_reachable())
        self.assertEqual(0, len(controller.get_running_instances_id_to_parameter()))
