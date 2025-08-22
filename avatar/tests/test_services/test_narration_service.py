import datetime

from avatar.messaging import *
from avatar.daemon import NarrationService, State, ImageService
from avatar.daemon.common.known_messages import UtteranceSequenceCommand
from unittest import TestCase

characters = ('c0', 'c1', 'c2')
activities = ('a0', 'a1', 'a2')

class NarrationTestCase(TestCase):
    def setUp(self):
        self.proc = AvatarDaemon(TestStream().create_client())
        self.state = State(character='c1', activity='a1')
        self.proc.rules.bind(NarrationService(
            self.state,
            characters,
            activities,
            UtteranceSequenceCommand('hello'),
            60,
            False
        ))

    def test_random_character_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand()).messages
        self.assertEqual(4, len(m))
        self.assertEqual('c0', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], ImageService.NewImageCommand)
        self.assertIsInstance(m[2], UtteranceSequenceCommand)


    def test_character_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand('c2')).messages
        print(m)
        self.assertEqual(4, len(m))
        self.assertEqual('c2', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], ImageService.NewImageCommand)
        self.assertIsInstance(m[2], UtteranceSequenceCommand)

    def test_random_activity_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeActivityCommand()).messages
        self.assertEqual(3, len(m))
        self.assertEqual('c1', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], ImageService.NewImageCommand)

    def test_activity_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeActivityCommand('a2')).messages
        self.assertEqual(3, len(m))
        self.assertEqual('c1', self.state.character)
        self.assertEqual('a2', self.state.activity)
        self.assertIsInstance(m[-2], ImageService.NewImageCommand)

    def test_time_ticks(self):
        d = datetime.datetime.now()
        m = self.proc.debug_and_stop_by_empty_queue(TimerEvent(d)).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TimerEvent(d+datetime.timedelta(seconds=1))).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TimerEvent(d+datetime.timedelta(seconds=59))).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TimerEvent(d+datetime.timedelta(seconds=60))).messages
        self.assertEqual(3, len(m))
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], ImageService.NewImageCommand)

        m = self.proc.debug_and_stop_by_empty_queue(TimerEvent(d+datetime.timedelta(seconds=120))).messages
        self.assertEqual(3, len(m))
        self.assertEqual('a1', self.state.activity)
        self.assertIsInstance(m[1], ImageService.NewImageCommand)

    def test_state_request(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.StateRequest()).messages
        for key, value in self.state.__dict__.items():
            self.assertEqual(value, m[-1].__dict__[key])








