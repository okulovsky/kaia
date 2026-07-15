from unittest import TestCase
from unittest.mock import MagicMock
from brainbox.framework.controllers.architecture import InstancesRegistry, DeciderInstance


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def execute(self, command, options=None):
        self.calls.append(tuple(command))
        return ''


class FakeController:
    def __init__(self, name='FakeController'):
        self._name = name
        self.executor = FakeExecutor()
        self._relevant_containers = ()

    def get_name(self):
        return self._name

    def get_executor(self):
        return self.executor

    def get_container_name(self, parameter):
        return f'{self._name}-{parameter}' if parameter is not None else self._name

    def get_image_source(self):
        source = MagicMock()
        source.get_relevant_containers.return_value = self._relevant_containers
        return source


class InstancesRegistryTestCase(TestCase):
    def test_register_deregister(self):
        registry = InstancesRegistry()
        controller = FakeController()
        instance = DeciderInstance(controller, None, 'abc123', 20000)
        registry.register(instance)
        self.assertEqual([instance], registry.get_instances())
        self.assertEqual(instance, registry.get_instance('abc123'))
        self.assertEqual(1, registry.count_instances('FakeController'))

        registry.deregister('abc123')
        self.assertEqual([], registry.get_instances())
        self.assertIsNone(registry.get_instance('abc123'))
        self.assertEqual(0, registry.count_instances('FakeController'))

    def test_allocate_port_skips_registered_and_reserved(self):
        registry = InstancesRegistry()
        controller = FakeController()
        registry.register(DeciderInstance(controller, None, 'inst-1', 20000))

        reserved_port = registry.allocate_port()
        self.assertNotEqual(20000, reserved_port)

        second_port = registry.allocate_port()
        self.assertNotEqual(reserved_port, second_port)
        self.assertNotEqual(20000, second_port)

        registry.release_port(reserved_port)
        registry.release_port(second_port)

    def test_allocate_port_reservation_is_released(self):
        registry = InstancesRegistry()
        port = registry.allocate_port()
        registry.release_port(port)
        port_again = registry.allocate_port()
        self.assertEqual(port, port_again)
        registry.release_port(port_again)

    def test_register_converts_reservation(self):
        registry = InstancesRegistry()
        controller = FakeController()
        port = registry.allocate_port()
        registry.register(DeciderInstance(controller, None, 'inst-1', port))
        # Port should no longer be "reserved" (it's now registered), but still unavailable
        next_port = registry.allocate_port()
        self.assertNotEqual(port, next_port)

    def test_count_instances_filters_by_controller_name(self):
        registry = InstancesRegistry()
        c1 = FakeController('ControllerOne')
        c2 = FakeController('ControllerTwo')
        registry.register(DeciderInstance(c1, None, 'a', 20000))
        registry.register(DeciderInstance(c2, None, 'b', 20001))
        registry.register(DeciderInstance(c1, 'param', 'c', 20002))

        self.assertEqual(2, registry.count_instances('ControllerOne'))
        self.assertEqual(1, registry.count_instances('ControllerTwo'))
        self.assertEqual(3, len(registry.get_instances()))

    def test_clean_up_kills_same_slot_and_deregisters(self):
        registry = InstancesRegistry()
        controller = FakeController()
        registry.register(DeciderInstance(controller, 'p1', 'inst-1', 20000))
        registry.register(DeciderInstance(controller, 'p2', 'inst-2', 20001))

        registry.clean_up(controller, 'p1')

        # The 'p1' slot instance should be deregistered, 'p2' instance should remain
        remaining_ids = {i.instance_id for i in registry.get_instances('FakeController')}
        self.assertEqual({'inst-2'}, remaining_ids)

        # docker stop/rm should have been called against the container name for parameter p1
        stop_calls = [c for c in controller.executor.calls if c[:2] == ('docker', 'stop')]
        self.assertTrue(any('FakeController-p1' in c for c in stop_calls))

    def test_clean_up_sweeps_orphans(self):
        registry = InstancesRegistry()
        controller = FakeController()
        controller._relevant_containers = ('orphan123', 'orphan456')
        registry.register(DeciderInstance(controller, None, 'orphan123', 20000))

        registry.clean_up(controller, 'unrelated_param')

        rm_calls = [c for c in controller.executor.calls if c[:2] == ('docker', 'rm')]
        rm_targets = {c[2] for c in rm_calls}
        # orphan123 is known (registered) so it should NOT be swept; orphan456 should be
        self.assertIn('orphan456', rm_targets)
        self.assertNotIn('orphan123', rm_targets)
