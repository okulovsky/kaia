from pathlib import Path
from unittest import TestCase

from avatar.daemon import (
    SoundInjectionCommand,
    SoundEvent,
    SetSilenceLevelCommand,
    StatefulRecorderStateEvent,
    StatefulRecorderState,
    InitializationEvent,
)
from avatar.utils import WebTestEnvironmentFactory, split_wav_by_amplitude, Sine

FOLDER = Path(__file__).parent / 'files'


class AutomatonTestCase(TestCase):
    def test_automaton(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('amp1000', Sine().segment(0.01).bytes())
            env.api.cache.upload('computer', (FOLDER / 'computer.wav').read_bytes())
            env.api.cache.upload('amp2500', Sine().segment(0.1).bytes())

            reader = env.client.clone_client()

            # Wait until WakeWordDetector has loaded the model
            env.client.query(120).where(lambda z: isinstance(z, InitializationEvent)).first()

            # Lower silence threshold so amp2500 registers as non-silence
            env.client.push(SetSilenceLevelCommand(level=0.04))

            # Standby: amp1000 is silence, recorder ignores it
            env.client.run_synchronously(SoundInjectionCommand('amp1000'), time_limit_in_seconds=30)

            # computer.wav triggers wake word → WaitingForSilence;
            # then FakeMicrophone feeds silence → openSlot.send() → FakeAudio confirms → Open
            env.client.run_synchronously(SoundInjectionCommand('computer'), time_limit_in_seconds=30)

            # Wait for StatefulRecorder to reach Open state before injecting speech
            open_event = None
            for msg in reader.query(time_limit_in_seconds=30, no_exception=True):
                if isinstance(msg, StatefulRecorderStateEvent) and msg.state == StatefulRecorderState.Open:
                    open_event = msg
                    break
            self.assertIsNotNone(open_event, 'StatefulRecorderStateEvent(Open) not received')

            # amp2500: non-silence → Record; silence when buffer exhausted → Commit
            env.client.run_synchronously(SoundInjectionCommand('amp2500'), time_limit_in_seconds=30)

            # Wait for SoundEvent (recorder committed)
            sound_event = None
            for msg in reader.query(time_limit_in_seconds=30, no_exception=True):
                if isinstance(msg, SoundEvent):
                    sound_event = msg
                    break
            self.assertIsNotNone(sound_event, 'SoundEvent not received')

            data = env.api.cache.read(sound_event.file_id)
            segments = split_wav_by_amplitude(data)
            non_silent = [s for s in segments if s.amplitude > 0.01]
            self.assertEqual(1, len(non_silent),
                             f'Expected exactly one non-silent segment (amp2500), got {non_silent}')

            snapshot = env.api.audio_dashboard_snapshot()
            (Path(__file__).parent / 'audio_dashboard_snapshot.png').write_bytes(snapshot)

HTML = '''
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import {
    AvatarClient, Dispatcher, FakeMicrophone, MicController,
    Recorder, StatefulRecorder, SilenceDetector, Automaton, AudioController,
    Message, Envelop, LoadingScreen
  } from '/frontend/scripts/kaia-frontend.js';
  import { KaldiWakeWordDetector } from '/frontend/scripts/kaldi-wake-word-detector.js';
  

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeMicrophone({ sampleRate: 22050, frameSize: 512, acceleration: 10, dispatcher, baseUrl: window.location.origin });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher });
  const silence = new SilenceDetector({ timeBetweenReportsInSeconds: 1, reportingWindowSeconds: 0.05, silenceLevel: 0.1, dispatcher });
  const wake = new KaldiWakeWordDetector({ sampleRateOfTheModel: 16000, words: ['computer'], modelUrl: '/frontend/models/vosk-model-small-en-us-0.15.zip', dispatcher });
  new AudioController({ dispatcher, baseUrl: window.location.origin, silent: true, acceleration: 10 });
  const automaton = new Automaton({ silenceDetector: silence, wakeWordDetector: wake, statefulRecorder: stateful, dispatcher });
  const controller = new MicController(input, m => automaton.process(m));

  dispatcher.start();
  const loadingDiv = document.createElement('div');
  document.body.appendChild(loadingDiv);
  new LoadingScreen(loadingDiv, [wake], () => {
    dispatcher.push(new Message('InitializationEvent', new Envelop(), {}));
    controller.start().catch(console.error);
  });
</script>
</body></html>
'''
