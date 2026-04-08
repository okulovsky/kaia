from pathlib import Path
from unittest import TestCase

from avatar.daemon.common.known_messages import SoundInjectionCommand, WakeWordEvent, SoundStreamingStartEvent, InitializationEvent
from avatar.utils import WebTestEnvironmentFactory, Sine



FOLDER = Path(__file__).parent / 'files'
ENABLE_DEBUG = 'false'

class WakeWordTestCase(TestCase):
    def test_wake_word_detected(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('noise', Sine().segment(0.5).bytes())
            env.api.cache.upload('computer', (FOLDER / 'computer.wav').read_bytes())

            reader = env.client.clone_client()

            # Wait until WakeWordDetector has loaded the model
            env.client.query(120).where(lambda z: isinstance(z, InitializationEvent)).first()

            FILE = None
            if ENABLE_DEBUG != 'false':
                FILE = reader.query(5).where(lambda z: isinstance(z, SoundStreamingStartEvent)).first().file_id

            # Feed noise — no wake word expected
            env.client.run_synchronously(SoundInjectionCommand('noise'), time_limit_in_seconds=30)
            messages = reader.pull(timeout_in_seconds=0)
            wake_words = [m for m in messages if isinstance(m, WakeWordEvent)]
            self.assertEqual(0, len(wake_words))

            # Feed computer.wav — wake word expected
            env.client.push(SoundInjectionCommand('computer'))
            found = None
            for msg in reader.query(time_limit_in_seconds=20, no_exception=True):
                if isinstance(msg, WakeWordEvent):
                    found = msg
                    break

            if FILE is not None:
                env.api.cache.download(FILE, Path(__file__).parent)

            self.assertIsNotNone(found)
            self.assertEqual('computer', found.word)




HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import { AvatarClient, Dispatcher, FakeMicrophone, MicController, Message, Envelop, LoadingScreen } from '/frontend/scripts/kaia-frontend.js';
  import { KaldiWakeWordDetector } from '/frontend/scripts/kaldi-wake-word-detector.js';
  
  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeMicrophone({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin });
  const wake = new KaldiWakeWordDetector({ sampleRateOfTheModel: 16000, words: ['computer'], modelUrl: '/frontend/models/vosk-model-small-en-us-0.15.zip', dispatcher, uploadDebugSound: ''' + ENABLE_DEBUG + ''' });
  const controller = new MicController(input, m => wake.detect(m));

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
