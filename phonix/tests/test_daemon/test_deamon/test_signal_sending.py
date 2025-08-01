from phonix.tests.test_daemon.test_deamon.common import *
from phonix.tests.test_daemon.test_deamon.audio_segmentation import Segment
from phonix.server.monitoring.plotting import PhonixMonitoring
from pathlib import Path
from datetime import datetime

class SignalSendingTestCase(TestCase):
    def test_signal_sending(self):
        with PhonixTestEnvironmentFactory(with_recording_server=True) as api:
            fname = api.recording_server.file_cache.upload(FileIO.read_bytes(PATH / 'computer_and_signal.wav'))
            api.client.put(SoundInjectionCommand(fname))

            q = api.client.query().feed(slice(lambda z: isinstance(z, SoundEvent)))
            recorded_file = api.recording_server.file_cache.download(q[-1].file_id)

            segments = Segment.analyze_wav(recorded_file, 100)
            target_segment = [s for s in segments if s.amplitude>0.7]
            self.assertEqual(1, len(target_segment))
            target_segment = target_segment[0]
            self.assertAlmostEqual(440, target_segment.frequency, 1)

            q += api.client.query().feed(slice(lambda z: isinstance(z, SoundConfirmation)))

            isinstance(q[0], SoundInjectionCommand)
            isinstance(q[1], WakeWordEvent)
            isinstance(q[2], SystemSoundCommand)
            isinstance(q[3], StateChange)
            isinstance(q[4], PlayStarted)
            isinstance(q[5], SoundConfirmation)
            isinstance(q[6], StateChange)
            isinstance(q[7], StateChange)
            isinstance(q[8], SystemSoundCommand)
            isinstance(q[9], SoundEvent)
            isinstance(q[10], StateChange)
            isinstance(q[11], PlayStarted)
            isinstance(q[12], Confirmation)
            isinstance(q[13], SoundConfirmation)





    def test_signal_sending_full(self):
        with PhonixTestEnvironmentFactory(with_recording_server=True, level_reporting=True) as api:
            fname = api.recording_server.file_cache.upload(FileIO.read_bytes(PATH / 'computer_and_signal.wav'))
            api.client.put(SoundInjectionCommand(fname))

            data = api.client.query().feed(slice(lambda z: isinstance(z, SoundEvent)))
            monitor = PhonixMonitoring(None, 10)
            monitor.create_figure_as_png(data, datetime.now(), Path(__file__).parent/'diagram.png', 800, 600)
