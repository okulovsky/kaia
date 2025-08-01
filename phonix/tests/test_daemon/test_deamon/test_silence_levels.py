from phonix.tests.test_daemon.test_deamon.common import *
from phonix.tests.test_daemon.test_deamon.audio_segmentation import Segment


class SignalSendingTestCase(TestCase):
    def test_signal_sending(self):
        with PhonixTestEnvironmentFactory(level_reporting=True) as api:
            api.client.put(SoundInjectionCommand('computer_and_signal.wav'))
            q = api.client.query().feed(slice(lambda z: isinstance(z, SoundEvent)))
            levels = [z.level for z in q if isinstance(z, SoundLevel)]
            self.assertGreater(len(levels), 40)

            levels = [z.silence_level for z in q if isinstance(z, SilenceLevelSet)]
            self.assertGreater(len(levels), 40)