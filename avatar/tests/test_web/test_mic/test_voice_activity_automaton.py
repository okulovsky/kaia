from unittest import TestCase

from avatar.daemon import SoundCommand, SoundConfirmation, SoundInjectionStartedEvent
from avatar.daemon.common.known_messages import SoundInjectionCommand, SoundStreamingEndEvent
from avatar.utils import Sine, WebTestEnvironment, WebTestEnvironmentFactory, split_wav_by_amplitude


class VoiceActivityAutomatonTestCase(TestCase):
    def _inject(self, env: WebTestEnvironment, sound: bytes, name: str = 'sample'):
        env.api.cache.upload(name, sound)
        env.client.push(SoundInjectionCommand(name))
        env.client.query(10).where(lambda z: isinstance(z, SoundInjectionStartedEvent)).first()

    def test_voice_opens_and_silence_commits(self):
        with WebTestEnvironmentFactory(HTML) as env:
            self._inject(
                env,
                (Sine()
                 .segment(0.01, 2)    # silence, the pre-roll buffer is filled
                 .segment(0.3, 2)     # voice, the recording starts
                 .segment(0.01, 2)    # silence, the recording is committed
                 .bytes())
            )
            end = None
            for message in env.client.query(20, no_exception=True):
                if isinstance(message, SoundStreamingEndEvent):
                    end = message
                    break
            self.assertIsNotNone(end, 'The recording was never committed')
            self.assertTrue(end.success)

            segments = split_wav_by_amplitude(env.api.cache.read(end.file_id))
            loud = [s for s in segments if s.amplitude > 0.03]
            self.assertEqual(1, len(loud), f'Expected exactly one non-silent segment, got {segments}')
            self.assertAlmostEqual(0.3, loud[0].amplitude, 1)
            self.assertAlmostEqual(2.0, loud[0].duration, 1)

    def test_playback_mutes_the_microphone(self):
        with WebTestEnvironmentFactory(HTML) as env:
            # 60 seconds of sound: the AudioController of this page runs at acceleration 10,
            # so the playback lasts ~6 real seconds, far longer than the injection below
            env.api.cache.upload('playback', Sine().segment(0.3, 60).bytes())
            env.client.push(SoundCommand('playback'))

            self._inject(
                env,
                (Sine()
                 .segment(0.01, 1)
                 .segment(0.3, 2)     # voice, but the avatar is talking, so it must be ignored
                 .segment(0.01, 1)
                 .bytes())
            )

            recordings = []
            confirmed = False
            for message in env.client.query(20, no_exception=True):
                if isinstance(message, SoundStreamingEndEvent):
                    recordings.append(message)
                if isinstance(message, SoundConfirmation):
                    confirmed = True
                    break
            self.assertTrue(confirmed, 'The playback was never confirmed')
            self.assertEqual([], recordings, 'The microphone recorded the playback')


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import {
    AvatarClient, Dispatcher, FakeMicrophone, MicController,
    Recorder, StatefulRecorder, SilenceDetector, VoiceActivityAutomaton, AudioController,
  } from '/frontend/scripts/kaia-frontend.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeMicrophone({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin, acceleration: 10 });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher });
  const silence = new SilenceDetector({ timeBetweenReportsInSeconds: 1, reportingWindowSeconds: 0.05, dispatcher });
  new AudioController({ dispatcher, baseUrl: window.location.origin, silent: true, acceleration: 10 });
  const automaton = new VoiceActivityAutomaton({ silenceDetector: silence, statefulRecorder: stateful, dispatcher });
  const controller = new MicController(input, m => automaton.process(m));

  dispatcher.start();
  controller.start().catch(console.error);
</script>
</body></html>
'''
