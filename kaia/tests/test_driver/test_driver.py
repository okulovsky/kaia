from kaia.driver import *
from eaglesong import Listen, Automaton, Return, Terminate
from grammatron import Template, Utterance, TemplatesCollection
from avatar.services import TextEvent, ChatCommand, UtteranceSequenceCommand
from avatar.messaging import TestStream, IMessage
from unittest import TestCase
from typing import cast

class Replies(TemplatesCollection):
    reply = Template("reply")

def test_routine():
    while True:
        value = yield
        if not isinstance(value, TextEvent):
            yield Listen()
            continue
        if value.text=='text':
            yield 'new_text'
        elif value.text == 'utterance':
            yield Replies.reply()
        elif value.text == 'sequence':
            yield Replies.reply()+"new_text"
        elif value.text == 'message':
            yield ChatCommand('command', ChatCommand.MessageType.system)
        elif value.text == 'error':
            yield Terminate('error')
        elif value.text == 'exit':
            yield Return()
        else:
            break
        yield Listen()

class DriverTestCase(TestCase):
    def check_ut(self, result: list[IMessage], *expected):
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[-1], UtteranceSequenceCommand)
        self.assertTrue(result[0].envelop.id, result[-1].envelop.reply_to)
        cmd = cast(UtteranceSequenceCommand, result[-1])
        self.assertEqual(len(expected), len(cmd.utterances_sequence.utterances))
        for e, a in zip(expected, cmd.utterances_sequence.utterances):
            if isinstance(e, Utterance):
                e.assertion(a, self)
            else:
                self.assertEqual(e, a)



    def test_driver(self):
        client = TestStream().create_client(None).with_name('main')
        driver = KaiaDriver(
            lambda _: test_routine,
            client.clone('driver'),
            expect_confirmations_for_types=()
        )
        driver.run_in_thread()
        client.put(TextEvent('text'))
        result = client.query(1).take(2).to_list()
        self.assertIsInstance(result[-1], UtteranceSequenceCommand)
        self.check_ut(result, 'new_text')

        client.put(TextEvent('utterance'))
        result = client.query(1).take(2).to_list()
        self.check_ut(result, Replies.reply())

        client.put(TextEvent('sequence'))
        result = client.query(1).take(2).to_list()
        self.check_ut(result, Replies.reply(), 'new_text')

        client.put(TextEvent('message'))
        result = client.query(1).take(2).to_list()
        self.assertIsInstance(result[-1], ChatCommand)
        self.assertEqual('command', result[-1].text)

        client.put(TextEvent('error'))
        result = client.query(1).take(2).to_list()
        self.assertIsInstance(result[-1], ChatCommand)
        self.assertTrue(result[-1].text.startswith('Error when handling'))

        client.put(TextEvent('exit'))
        with self.assertRaises(ValueError):
            client.query(1).take(2).to_list()








