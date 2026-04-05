from pathlib import Path
from unittest import TestCase

from selenium.webdriver.support.ui import WebDriverWait

from avatar.daemon import (
    SoundInjectionCommand,
    SoundEvent,
    SetSilenceLevelCommand,
    StatefulRecorderStateEvent,
    StatefulRecorderState
)
from avatar.utils.web_test_environment import WebTestEnvironmentFactory
from avatar.utils.wav_utils import split_wav_by_amplitude
from avatar.utils.sine_wav import sine_wav

FOLDER = Path(__file__).parent / 'files'


class AutomatonTestCase(TestCase):
    def test_automaton(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('amp1000', sine_wav(1000))
            env.api.cache.upload('computer', (FOLDER / 'computer.wav').read_bytes())
            env.api.cache.upload('amp2500', sine_wav(2500))

            reader = env.client.clone()

            WebDriverWait(env.driver, 120).until(
                lambda d: d.execute_script('return window.voskReady === true')
            )

            # Lower silence threshold so amp2500 registers as non-silence
            env.client.push(SetSilenceLevelCommand(level=0.04))

            # Standby: amp1000 is silence, recorder ignores it
            env.client.run_synchronously(SoundInjectionCommand('amp1000'), time_limit_in_seconds=30)

            # computer.wav triggers wake word → WaitingForSilence;
            # then FakeInput feeds silence → openSlot.send() → FakeAudio confirms → Open
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
            non_silent = [s for s in segments if s > 0.01]
            self.assertEqual(1, len(non_silent),
                             f'Expected exactly one non-silent segment (amp2500), got {non_silent}')

            snapshot = env.api.audio_dashboard_snapshot()
            (Path(__file__).parent / 'audio_dashboard_snapshot.png').write_bytes(snapshot)


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import {
    AvatarClient, Dispatcher, FakeInput, MicController,
    Recorder, StatefulRecorder, SilenceDetector, Automaton, FakeAudio,
  } from '/frontend/scripts/index.js';
  import { WakeWordDetector } from '/frontend/scripts/wakeWordDetector.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeInput({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher });
  const silence = new SilenceDetector({ timeBetweenReportsInSeconds: 1, discretizationInSeconds: 0.05, dispatcher });
  const wake = new WakeWordDetector({ sampleRateOfTheModel: 16000, words: ['computer'], modelUrl: '/frontend/models/vosk-model-small-en-us-0.15.zip', dispatcher });
  const fakeAudio = new FakeAudio({ dispatcher });
  const automaton = new Automaton({ silenceDetector: silence, wakeWordDetector: wake, statefulRecorder: stateful, dispatcher });
  const controller = new MicController(input, m => automaton.process(m));

  dispatcher.start();
  controller.start().catch(console.error);

  const readyCheck = setInterval(() => {
    if (wake.isInitialized()) {
      window.voskReady = true;
      clearInterval(readyCheck);
    }
  }, 500);
</script>
</body></html>
'''
