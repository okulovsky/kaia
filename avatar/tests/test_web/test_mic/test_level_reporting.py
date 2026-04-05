from unittest import TestCase
from avatar.daemon.common.known_messages import SoundInjectionCommand, SetSilenceLevelCommand
from avatar.utils.web_test_environment import WebTestEnvironmentFactory
from avatar.daemon.common import SoundLevelReport
from pathlib import Path
from avatar.messaging import AvatarClient
from avatar.utils import Sine
import numpy as np

FOLDER = Path(__file__).parent/'files'

def slice(client: AvatarClient):
    EPS = 0.0001
    found = False
    result = []
    for data in client.query(time_limit_in_seconds=30, no_exception=True):
        if not isinstance(data, SoundLevelReport):
            continue
        level = np.mean(data.levels)
        print(level)
        if level < EPS:
            if found:
                return result
        else:
            result.append(level)
            found = True
    return result


class LevelReportingTestCase(TestCase):
    def test_louder_sample_reports_higher_level(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('sample1', Sine().segment(0.1).bytes())
            env.api.cache.upload('sample2', Sine().segment(0.5).bytes())
            reader = env.client.clone()

            env.client.run_synchronously(SoundInjectionCommand('sample1'), time_limit_in_seconds=30)
            levels1 = slice(reader)

            env.client.run_synchronously(SoundInjectionCommand('sample2'), time_limit_in_seconds=30)
            levels2 = slice(reader)

        self.assertGreater(len(levels1), 0)
        self.assertGreater(len(levels2), 0)
        avg1 = np.mean(levels1)
        avg2 = np.mean(levels2)
        self.assertGreater(avg2, avg1)

    def test_silence_level_is_reported(self):
        with WebTestEnvironmentFactory(HTML) as env:
            reader = env.client.clone()

            env.client.push(SetSilenceLevelCommand(level=0.5))

            for report in reader.query(time_limit_in_seconds=5, no_exception=True):
                if not isinstance(report, SoundLevelReport):
                    continue
                if report.silence_level == 0.5:
                    return

        self.fail("No SoundLevelReport with silence_level=0.5 received")


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import { AvatarClient, Dispatcher, FakeInput, MicController, SilenceDetector } from '/frontend/scripts/index.js';

  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeInput({ sampleRate: 22050, frameSize: 512, acceleration: 10, dispatcher, baseUrl: window.location.origin });
  const levels = new SilenceDetector({ timeBetweenReportsInSeconds: 0.5, reportingWindowSeconds: 0.05, dispatcher });
  const controller = new MicController(input, m => levels.detect(m));
  dispatcher.start();
  controller.start().catch(console.error);
</script>
</body></html>
'''
