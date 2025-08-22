from phonix.tests.test_daemon.test_deamon.common import *

class WakeWordTestCase(TestCase):
    def test_wake_word(self):
        with PhonixTestEnvironmentFactory() as api:
            injection = api.client.put(SoundInjectionCommand('computer.wav'))

            q = api.client.query(1).feed(slice(lambda z: z.is_confirmation_of(injection)))
            print(q) # Sound Confirmation and only then Injection confirmation, why?
            self.assertEqual(7, len(q))
            self.assertIsInstance(q[0], SoundInjectionCommand)
            self.assertIsInstance(q[1], WakeWordEvent)
            self.assertIsInstance(q[2], SystemSoundCommand)
            self.assertIsInstance(q[3], MicStateChangeReport)
            self.assertIsInstance(q[4], SoundPlayStarted)
            self.assertIsInstance(q[5], SoundConfirmation)
            self.assertTrue(q[5].is_confirmation_of(q[4]))
            self.assertTrue(q[5].is_confirmation_of(q[2]))
            self.assertIsInstance(q[6], Confirmation)



    def test_no_wake_word(self):
        with PhonixTestEnvironmentFactory() as api:
            injection = api.client.put(SoundInjectionCommand('sandwich.wav'))

            q = api.client.query(1).feed(slice(lambda z: z.is_confirmation_of(injection)))
            self.assertEqual(2, len(q))
            self.assertIsInstance(q[0], SoundInjectionCommand)
            self.assertIsInstance(q[1], Confirmation)








