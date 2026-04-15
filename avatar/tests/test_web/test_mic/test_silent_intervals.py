from pathlib import Path
from unittest import TestCase

from selenium.webdriver.support.ui import WebDriverWait

from avatar.daemon import SoundLevelReport, SoundInjectionStartedEvent
from avatar.daemon.common.known_messages import SoundInjectionCommand, SoundStreamingEndEvent, OpenMicCommand
from avatar.messaging import IMessage
from avatar.utils import WebTestEnvironmentFactory, Sine, WebTestEnvironment, split_wav_by_amplitude



FOLDER = Path(__file__).parent / 'files'


class SilenceMarginsTestCase(TestCase):
    def _run(self, env: WebTestEnvironment, sound: bytes):
        env.api.cache.upload('sample', sound)
        env.client.push(SoundInjectionCommand('sample'))
        env.client.query(10).where(lambda z: isinstance(z, SoundInjectionStartedEvent)).first()
        env.client.push(OpenMicCommand())
        messages = []
        for m in env.client.query(10, no_exception=True):
            messages.append(m)
            if isinstance(m, SoundStreamingEndEvent):
                break
        return messages

    def print_messages(self, messages: list[IMessage]):
        first_timestamp = None
        for m in messages:
            if isinstance(m, OpenMicCommand):
                first_timestamp = m.envelop.timestamp
            if first_timestamp is None:
                continue
            delta = (m.envelop.timestamp - first_timestamp).total_seconds()
            if isinstance(m, SoundLevelReport):
                payload = m.decision_level
            else:
                payload = str(m)
            print(f'{delta} - {payload}')



    def test_simple_case(self):
        with WebTestEnvironmentFactory(HTML(10)) as env:
            sound = (Sine()
                     .segment(0.5, 4) #loud, the opening can't happen
                     .segment(0.01, 3) # silence and long enough for opening + to fill the buffer in stateful recorder
                     .segment(0.3, 2) #loud, the recording should start
                     .segment(0.01, 1.5) # silence, the recording should finish
                     .bytes()
                     )
            messages = self._run(env, sound)
            self.print_messages(messages)
            self.assertIsInstance(messages[-1], SoundStreamingEndEvent)
            data = env.api.cache.read(messages[-1].file_id)
            #with open(Path(__file__).parent/'sample.wav', 'wb') as f:
            #    f.write(data)
            segments = split_wav_by_amplitude(data)

            self.assertEqual(3, len(segments))
            self.assertAlmostEqual(0.3, segments[1].amplitude, 1)
            self.assertAlmostEqual(2.0, segments[1].duration, 1)
            self.assertGreater(0.03, segments[0].amplitude)
            self.assertGreater(0.03, segments[2].amplitude)








def HTML(maxNonSilenceAfterWakeWordTillReset = 1):
    return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import {
    AvatarClient, Dispatcher, FakeMicrophone, MicController,
    Recorder, StatefulRecorder, SilenceDetector, Automaton, AudioController,
  } from '/frontend/scripts/kaia-frontend.js';
  import { KaldiWakeWordDetector } from '/frontend/scripts/kaldi-wake-word-detector.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeMicrophone({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin, acceleration: 10 });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher });
  const silence = new SilenceDetector({ timeBetweenReportsInSeconds: 1, reportingWindowSeconds: 0.05, dispatcher });
  new AudioController({ dispatcher, baseUrl: window.location.origin, silent: true, acceleration: 10});
  const automaton = new Automaton({ 
    silenceDetector: silence, 
    wakeWordDetector: null, 
    statefulRecorder: stateful,
    dispatcher,
    maxNonSilenceAfterWakeWordTillReset: ''' + str(maxNonSilenceAfterWakeWordTillReset) + '''
    }); // TODO: make it possible for wakeWordDetector to be null
  const controller = new MicController(input, m => automaton.process(m));

  dispatcher.start();
  controller.start().catch(console.error);

</script>
</body></html>
'''
