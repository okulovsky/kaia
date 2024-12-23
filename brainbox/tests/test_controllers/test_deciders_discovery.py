from brainbox.deciders import Boilerplate
from unittest import TestCase
from brainbox.framework import ControllerRegistry

class DecidersDiscoveryTestCase(TestCase):
    def test(self):
        registry = ControllerRegistry.discover_or_create(None)
        controller = registry.get_controller('Boilerplate')
        self.assertIsInstance(controller, Boilerplate.Controller)

