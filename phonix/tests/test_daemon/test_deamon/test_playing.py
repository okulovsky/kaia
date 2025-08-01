from phonix.tests.test_daemon.test_deamon.common import *

class MicClosingTestCase(TestCase):
    def test_playing_one_record(self):
        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            api.client.put(SoundCommand('computer.wav'))
            q = api.client.query(1).take(4).to_list()
            self.assertIsInstance(q[1], PlayStarted)
            self.assertIsInstance(q[2], SoundConfirmation)
            self.assertIsInstance(q[3], SoundConfirmation)
            self.assertTrue(q[2].is_confirmation_of(q[0]))
            self.assertTrue(q[3].is_confirmation_of(q[1]))

    def test_playing_two_records(self):
        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            api.client.put(SoundCommand('computer.wav', 'first'))
            api.client.put(SoundCommand('computer.wav', 'second'))
            q = api.client.query(1).take(8).to_list()

            self.assertIsInstance(q[2], PlayStarted)
            self.assertIsInstance(q[3], SoundConfirmation)
            self.assertIsInstance(q[4], SoundConfirmation)
            self.assertTrue(q[3].is_confirmation_of(q[0]))
            self.assertTrue(q[4].is_confirmation_of(q[2]))
            self.assertTrue(q[3].terminated)
            self.assertTrue(q[4].terminated)

            self.assertIsInstance(q[5], PlayStarted)
            self.assertIsInstance(q[6], SoundConfirmation)
            self.assertIsInstance(q[7], SoundConfirmation)
            self.assertTrue(q[6].is_confirmation_of(q[1]))
            self.assertTrue(q[7].is_confirmation_of(q[5]))
            self.assertFalse(q[6].terminated)
            self.assertFalse(q[7].terminated)



