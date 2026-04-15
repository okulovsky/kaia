from time import sleep
from unittest import TestCase

from avatar.daemon import SoundCommand, SoundConfirmation
from avatar.utils import WebTestEnvironmentFactory, Sine



class RealAudioTestCase(TestCase):
    def test_interruption(self):
        with WebTestEnvironmentFactory(HTML) as env:
            # 3-second file for the first command so it's still playing when interrupted
            env.api.cache.upload('long', Sine().segment(0.5, 100.0).bytes())
            # 1-second file for the second command
            env.api.cache.upload('short', Sine().segment(0.3, 2).bytes())

            reader = env.client.clone_client()

            cmd_a = SoundCommand(file_id='long')
            env.client.push(cmd_a)

            # Give the browser time to fetch + decode + start playing before interrupting
            sleep(0.5)

            cmd_b = SoundCommand(file_id='short')
            env.client.push(cmd_b)

            # Collect exactly 2 SoundConfirmations (terminated + completed)
            confirmations = []
            for msg in reader.query(time_limit_in_seconds=10, no_exception=True):
                if isinstance(msg, SoundConfirmation):
                    confirmations.append(msg)
                if len(confirmations) == 2:
                    break

            self.assertEqual(2, len(confirmations),
                             f'Expected 2 SoundConfirmations, got {len(confirmations)}')

            conf_a = next((c for c in confirmations if c.is_confirmation_of(cmd_a)), None)
            conf_b = next((c for c in confirmations if c.is_confirmation_of(cmd_b)), None)

            self.assertIsNotNone(conf_a, 'No SoundConfirmation received for cmd_a')
            self.assertIsNotNone(conf_b, 'No SoundConfirmation received for cmd_b')
            self.assertTrue(conf_a.terminated,
                            'cmd_a should be terminated=True (it was interrupted)')
            self.assertFalse(conf_b.terminated,
                             'cmd_b should be terminated=False (it played to completion)')


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import { AvatarClient, Dispatcher, AudioController } from '/frontend/scripts/kaia-frontend.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  new AudioController({ dispatcher, baseUrl: window.location.origin, silent: true });
  dispatcher.start();
</script>
</body></html>
'''
