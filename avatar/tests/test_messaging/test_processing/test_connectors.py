import time
from unittest import TestCase
from dataclasses import dataclass
from avatar.messaging import *


@dataclass
class Message(IMessage):
    value: int

def handler_1(m: Message) -> Message:
    return Message(m.value+1)

def handler_2(m: Message) -> Message:
    time.sleep(0.1)
    return Message(m.value*10)

class RuleConnectorTestCase(TestCase):
    def check(self, second_rule_connector_factory):
        client = TestStream().create_client()
        avatar = AvatarProcessor(client)
        first_rule = avatar.rules.add(handler_1, 'input')
        avatar.rules.add(handler_2, second_rule_connector_factory(first_rule))
        client.put(Message(1).as_from_publisher('input'))
        result = avatar.debug_and_stop_by_count(2)
        return [e.value for e in result.messages[1:]]

    def test_1(self):
        result = self.check(lambda _:'input')
        self.assertEqual([2, 10], result)

    def test_2(self):
        result = self.check(lambda r: r.name)
        self.assertEqual([2,20], result)

    def test_3(self):
        result = self.check(lambda r: r)
        self.assertEqual([2,20], result)




