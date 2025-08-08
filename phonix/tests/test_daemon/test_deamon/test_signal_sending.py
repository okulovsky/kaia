from phonix.tests.test_daemon.test_deamon.common import *
from phonix.tests.test_daemon.test_deamon.audio_segmentation import Segment
from pathlib import Path
from avatar.messaging.amenities import ThreadCollection


class SignalSendingTestCase(TestCase):
    def test_signal_sending(self):
        with PhonixTestEnvironmentFactory(with_recording_server=True) as api:
            fname = api.api.file_cache.upload(FileIO.read_bytes(PATH / 'computer_and_signal.wav'))
            api.client.put(SoundInjectionCommand(fname))

            q = api.client.query(10).feed(slice(lambda z: isinstance(z, SoundEvent)))
            recorded_file = api.api.file_cache.download(q[-1].file_id)

            segments = Segment.analyze_wav(recorded_file, 100)
            target_segment = [s for s in segments if s.amplitude>0.7]
            self.assertEqual(1, len(target_segment))
            target_segment = target_segment[0]
            self.assertAlmostEqual(440, target_segment.frequency, 1)

            q += api.client.query(5).feed(slice(lambda z: isinstance(z, SoundConfirmation)))


            isinstance(q[0], SoundInjectionCommand)
            isinstance(q[1], WakeWordEvent)
            isinstance(q[2], SystemSoundCommand)
            isinstance(q[3], MicStateChangeReport)
            isinstance(q[4], SoundPlayStarted)
            isinstance(q[5], SoundConfirmation)
            isinstance(q[6], MicStateChangeReport)
            isinstance(q[7], MicStateChangeReport)
            isinstance(q[8], SystemSoundCommand)
            isinstance(q[9], SoundEvent)
            isinstance(q[10], MicStateChangeReport)
            isinstance(q[11], SoundPlayStarted)
            isinstance(q[12], Confirmation)
            isinstance(q[13], SoundConfirmation)

            FileIO.write_bytes(api.api.get_snapshot(), Path(__file__).parent / 'diagram_1.png')

            ThreadCollection.just_print(q)

    def test_two_sendings(self):
        with PhonixTestEnvironmentFactory(with_recording_server=True) as api:
            tracks = []
            for i in range(2):
                fname = api.api.file_cache.upload(FileIO.read_bytes(PATH / 'computer_and_signal.wav'))
                api.client.put(SoundInjectionCommand(fname))
                tracks.append(api.client.query(10).where(lambda z: isinstance(z, SoundConfirmation)).take(1).to_list())

            for first, second in zip(tracks[0], tracks[1]):
                self.assertTrue(type(first) is type(second))



