from pathlib import Path
from unittest import TestCase

from selenium.webdriver.support.ui import WebDriverWait

from avatar.daemon.common.known_messages import SoundInjectionCommand, WakeWordEvent, SoundStartEvent
from avatar.utils.web_test_environment import WebTestEnvironmentFactory
from avatar.utils.sine_wav import sine_wav


FOLDER = Path(__file__).parent / 'files'
ENABLE_DEBUG = 'false'

class WakeWordTestCase(TestCase):
    def test_wake_word_detected(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('noise', sine_wav(1000))
            env.api.cache.upload('computer', (FOLDER / 'computer.wav').read_bytes())

            reader = env.client.clone()

            # Wait until VoskWakeWordUnit has loaded the model
            WebDriverWait(env.driver, 120).until(
                lambda d: d.execute_script('return window.voskReady === true')
            )

            FILE = None
            if ENABLE_DEBUG != 'false':
                FILE = reader.query(5).where(lambda z: isinstance(z, SoundStartEvent)).first().file_id

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
  import { AvatarClient, Dispatcher, FakeInput, MicController } from '/frontend/scripts/index.js';
  import { WakeWordDetector } from '/frontend/scripts/wakeWordDetector.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeInput({ sampleRate: 22050, frameSize: 512, dispatcher, baseUrl: window.location.origin });
  const wake = new WakeWordDetector({ sampleRateOfTheModel: 16000, words: ['computer'], modelUrl: '/frontend/models/vosk-model-small-en-us-0.15.zip', dispatcher, uploadDebugSound: ''' + ENABLE_DEBUG + ''' });
  const controller = new MicController(input, m => wake.detectWakeWord(m));

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
