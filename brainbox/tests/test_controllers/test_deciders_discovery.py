from brainbox.deciders import HelloBrainBox, Collector
from unittest import TestCase
from brainbox.framework import ControllerRegistry, ControllerOverDecider

class DecidersDiscoveryTestCase(TestCase):
    #TODO: Add the tests on ControllerRegistry.to_controller to other types of acceptable ControllerLike-types

    def test_automatic_discovery(self):
        registry = ControllerRegistry.discover_or_create(None)
        controller = registry.get_controller('HelloBrainBox')
        self.assertIsInstance(controller, HelloBrainBox.Controller)
        controller = registry.get_controller('Collector')
        self.assertIsInstance(controller, ControllerOverDecider)
        self.assertIsInstance(controller.decider, Collector)

