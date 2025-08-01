from phonix.tests.test_daemon.test_deamon.common import *

class MicClosingTestCase(TestCase):
    def test_wake_word_then_silence(self):

        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            injection = api.client.put(SoundInjectionCommand('computer.wav'))

            api.client.query(1).feed(slice(lambda z: z.is_confirmation_of(injection)))
            api.client.query(1).feed(slice(lambda z: isinstance(z, SoundConfirmation)))

            q = api.client.query(1).feed(slice(lambda z: isinstance(z, SoundConfirmation)))

            self.assertEqual(4, len(q))
            self.assertIsInstance(q[0], SystemSoundCommand)
            self.assertIsInstance(q[1], StateChange)
            self.assertIsInstance(q[2], PlayStarted)
            self.assertIsInstance(q[3], SoundConfirmation)

