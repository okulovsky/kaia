from phonix.tests.test_daemon.test_deamon.common import *
from pprint import pprint

class MicClosingTestCase(TestCase):
    def test_wake_word_then_silence(self):

        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            injection = api.client.put(SoundInjectionCommand('computer.wav'))

            wake_word_epoch = api.client.query(1).feed(slice(lambda z: z.is_confirmation_of(injection)))
            q = api.client.query(1).feed(slice(lambda z: isinstance(z, SoundConfirmation)))

            pprint(q)

            self.assertEqual(5, len(q))
            self.assertIsInstance(q[0], MicStateChangeReport)
            self.assertIsInstance(q[1], SystemSoundCommand)
            self.assertIsInstance(q[2], MicStateChangeReport)
            self.assertIsInstance(q[3], SoundPlayStarted)
            self.assertIsInstance(q[4], SoundConfirmation)

