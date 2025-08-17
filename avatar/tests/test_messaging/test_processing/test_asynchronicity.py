import unittest
import asyncio
import time
from dataclasses import dataclass
from avatar.messaging import AvatarDaemon, Rule, IMessage, TestStream, BindingSettings


@dataclass
class In(IMessage):
    content: str

@dataclass
class Out(IMessage):
    value: int


class Handlers1:
    def handler_1_1(self, msg: In) -> Out:
        time.sleep(0.2)
        return Out(value=1)

    def handler_1_2(self, msg: In) -> Out:
        time.sleep(0.2)
        return Out(value=2)

class Handlers2:
    def handler_2_1(self, msg: In) -> Out:
        time.sleep(0.2)
        return Out(value=1)

    def handler_2_2(self, msg: In) -> Out:
        time.sleep(0.2)
        return Out(value=2)



class TestStreamProcessor(unittest.TestCase):
    def check(self, functions, messages_count = 1, asynchronous = False):
        stream = TestStream()
        client = stream.create_client()
        messages = [In(content="hello") for _ in range(messages_count)]
        for m in messages:
            client.put(m)

        processor = AvatarDaemon(
            client,
        )
        for f in functions:
            processor.rules.bind(f, BindingSettings().asynchronous(asynchronous))

        result = processor.debug_and_stop_by_count(len(functions)*messages_count)
        return result.duration


    def test_one_handler(self):
        delta = self.check([Handlers1().handler_1_1])
        self.assertTrue(0.2<=delta<=0.3)

    def test_sequencial_handler(self):
        h = Handlers1()
        delta = self.check([h.handler_1_1, h.handler_1_2])
        print(delta)
        self.assertTrue(0.4<=delta<=0.5)

    def test_parallel_handlers(self):
        delta = self.check([Handlers1().handler_1_1, Handlers2().handler_2_1])
        print(delta)
        self.assertTrue(0.2 <= delta <= 0.3)

    def test_splitted_objects_parallelism(self):
        delta = self.check([Handlers1().handler_1_1, Handlers1().handler_1_2])
        self.assertTrue(0.2 <= delta <= 0.3)

    def test_asynchronysity_off(self):
        delta = self.check([Handlers1().handler_1_1], 3)
        self.assertTrue(0.6 <= delta <= 0.7)

    def test_asynchronysity_on(self):
        delta = self.check([Handlers1().handler_1_1], 3, asynchronous=True)
        self.assertTrue(0.2 <= delta <= 0.3)
