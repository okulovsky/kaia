from avatar.messaging.rules.rule_collection import RulesCollection, BindingSettings
from avatar.messaging import IService, message_handler
from unittest import TestCase

class TestService(IService):
    @message_handler
    def a(self, message: int) -> float:
        return message

    @message_handler
    def b(self, message: int):
        return message-1

    @message_handler
    def c(self, message: str) -> float:
        return float(message)

class OtherService:
    pass

class RuleCreatorTestCase(TestCase):
    def test_binding(self):
        c = RulesCollection()
        c.bind(TestService())

        self.assertEqual(3, len(c.rules))

        self.assertEqual('TestService/a', c.rules[0].name)
        self.assertEqual(int, c.rules[0].input.type)
        self.assertIsNone(c.rules[0].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[0].input.exclude_publisher_prefixes)

        self.assertEqual('TestService/b', c.rules[1].name)
        self.assertEqual(int, c.rules[1].input.type)
        self.assertIsNone(c.rules[1].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[1].input.exclude_publisher_prefixes)

        self.assertEqual('TestService/c', c.rules[2].name)
        self.assertEqual(str, c.rules[2].input.type)
        self.assertIsNone(c.rules[2].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[2].input.exclude_publisher_prefixes)

    def test_binding_of_1(self):
        c = RulesCollection()
        c.bind(TestService().a)
        self.assertEqual(1, len(c.rules))
        self.assertEqual('TestService/a', c.rules[0].name)
        self.assertEqual(int, c.rules[0].input.type)
        self.assertIsNone(c.rules[0].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[0].input.exclude_publisher_prefixes)

    def test_binding_with_type_setting(self):
        c = RulesCollection()
        service = TestService()
        service.binding_settings.bind_type(int).to(OtherService)
        c.bind(service)
        self.assertEqual(('OtherService',), c.rules[0].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[0].input.exclude_publisher_prefixes)

        self.assertEqual(('OtherService',), c.rules[1].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[1].input.exclude_publisher_prefixes)

        self.assertIsNone(c.rules[2].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[2].input.exclude_publisher_prefixes)


    def test_binding_with_method_setting_exclusion(self):
        c = RulesCollection()
        service = TestService()
        service.binding_settings.bind_method(TestService.a).to_all_except(OtherService)
        c.bind(service)
        self.assertIsNone(c.rules[0].input.include_publisher_prefixes)
        self.assertEqual(('OtherService',), c.rules[0].input.exclude_publisher_prefixes)

        self.assertIsNone(c.rules[1].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[1].input.exclude_publisher_prefixes)

        self.assertIsNone(c.rules[2].input.include_publisher_prefixes)
        self.assertIsNone(c.rules[2].input.exclude_publisher_prefixes)

    def test_async(self):
        c = RulesCollection()
        service = TestService()
        service.binding_settings.asynchronous()
        c.bind(service)
        for rule in c.rules:
            self.assertTrue(rule.asynchronous)


    def test_async_from_provided_settings(self):
        c = RulesCollection()
        service = TestService()
        service.binding_settings.asynchronous()
        c.bind(service, BindingSettings())
        for rule in c.rules:
            self.assertFalse(rule.asynchronous)


