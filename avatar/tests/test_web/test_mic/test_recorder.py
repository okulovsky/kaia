from unittest import TestCase

from avatar.daemon.common.known_messages import (
    SoundInjectionCommand,
    SoundStartEvent,
    SoundEvent,
    StatefulRecorderStateCommand,
    StatefulRecorderState
)
from avatar.utils.web_test_environment import WebTestEnvironmentFactory
from avatar.utils.wav_utils import split_wav_by_amplitude
from avatar.utils.sine_wav import sine_wav



class RecorderTestCase(TestCase):
    def test_recorder(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('amp1000', sine_wav(1000))
            env.api.cache.upload('amp2500', sine_wav(2500))
            env.api.cache.upload('amp5000', sine_wav(5000))

            reader = env.client.clone()

            # Standby: amp1000 should be ignored by the recorder
            env.client.run_synchronously(SoundInjectionCommand('amp1000'), time_limit_in_seconds=30)

            # Open: amp2500 accumulates in startBuffer as pre-roll
            env.client.push(StatefulRecorderStateCommand(state=StatefulRecorderState.Open))
            env.client.run_synchronously(SoundInjectionCommand('amp2500'), time_limit_in_seconds=30)

            # Record: triggers _firstWrite on the next MicController tick
            env.client.push(StatefulRecorderStateCommand(state=StatefulRecorderState.Record))

            # Wait for SoundStartEvent — guarantees header + pre-roll are on disk
            start_event: SoundStartEvent | None = None
            for msg in reader.query(time_limit_in_seconds=30, no_exception=True):
                if isinstance(msg, SoundStartEvent):
                    start_event = msg
                    break
            self.assertIsNotNone(start_event, 'SoundStartEvent not received')

            # Snapshot 1: pre-roll only (amp2500)
            snapshot1 = env.api.cache.read(start_event.file_id)

            # Recording: amp5000 is written to the file
            env.client.run_synchronously(SoundInjectionCommand('amp5000'), time_limit_in_seconds=30)

            # Commit: flushes remaining buffer, fires SoundEvent
            env.client.push(StatefulRecorderStateCommand(state=StatefulRecorderState.Commit))

            sound_event: SoundEvent | None = None
            for msg in reader.query(time_limit_in_seconds=30, no_exception=True):
                if isinstance(msg, SoundEvent):
                    sound_event = msg
                    break
            self.assertIsNotNone(sound_event, 'SoundEvent not received')

            # Snapshot 2: pre-roll + amp5000
            snapshot2 = env.api.cache.read(sound_event.file_id)

        # --- Verify snapshot 1 ---
        segments1 = split_wav_by_amplitude(snapshot1)
        non_silent1 = [s for s in segments1 if s > 0.01]
        self.assertGreater(len(non_silent1), 0, 'Snapshot 1 has no non-silent segments')
        self.assertEqual(1, len(non_silent1),
                         f'Snapshot 1 should have exactly one non-silent segment, got {non_silent1}')

        # --- Verify snapshot 2 ---
        segments2 = split_wav_by_amplitude(snapshot2)
        non_silent2 = [s for s in segments2 if s > 0.01]
        self.assertEqual(2, len(non_silent2),
                         f'Snapshot 2 should have two non-silent segments (amp2500 + amp5000), got {non_silent2}')
        # amp5000 segment should be louder than amp2500 segment
        self.assertGreater(non_silent2[1], non_silent2[0],
                           'Second segment should be louder (amp5000 > amp2500)')


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import { AvatarClient, Dispatcher, FakeInput, MicController, Recorder, StatefulRecorder } from '/frontend/scripts/index.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeInput({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher, subscribeToDirectStateChange: true });
  const controller = new MicController(input, m => stateful.process(m));
  dispatcher.start();
  controller.start().catch(console.error);
</script>
</body></html>
'''
