from phonix.tests.test_daemon.test_deamon.common import *

class MicClosingTestCase(TestCase):
    def test_playing_one_record(self):
        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            api.client.put(SoundCommand('computer.wav'))
            q = api.client.query(1).take(3).to_list()
            self.assertIsInstance(q[1], SoundPlayStarted)
            self.assertIsInstance(q[2], SoundConfirmation)
            self.assertTrue(q[2].is_confirmation_of(q[0]))
            self.assertTrue(q[2].is_confirmation_of(q[1]))

    def test_playing_two_records(self):
        with PhonixTestEnvironmentFactory(waiting_time_to_close_the_mic=0.5) as api:
            api.client.put(SoundCommand('computer.wav', 'first'))
            api.client.put(SoundCommand('computer.wav', 'second'))
            q = api.client.query(1).take(6).to_list()

            self.assertIsInstance(q[2], SoundPlayStarted)
            self.assertIsInstance(q[3], SoundConfirmation)
            self.assertTrue(q[3].is_confirmation_of(q[0]))
            self.assertTrue(q[3].is_confirmation_of(q[2]))
            self.assertTrue(q[3].terminated)

            self.assertIsInstance(q[4], SoundPlayStarted)
            self.assertIsInstance(q[5], SoundConfirmation)
            self.assertTrue(q[5].is_confirmation_of(q[1]))
            self.assertTrue(q[5].is_confirmation_of(q[4]))
            self.assertFalse(q[5].terminated)
            self.assertFalse(q[5].terminated)



