from unittest import TestCase
from avatar.daemon import *
from kaia.app import ServerStartedEvent
from kaia.utils import BackendTestEnvironmentFactory
from avatar.utils import FrontendTestEnvironmentFactory
from pathlib import Path

def file(s: str):
    return Path(__file__).parent / 'files' / (s+'.wav')

class BackendAndFrontendInitializationTestCase(TestCase):
    def test_backend_and_frontend(self):
        with BackendTestEnvironmentFactory(self, html=HTML(0.01)) as env:
            with FrontendTestEnvironmentFactory(env.base_url, headless=True) as driver:
                try:
                    env.client.wait_for_availability()
                    env.client.scroll_to_end()
                    env.parse_reaction(
                        TextCommand)  # "Hello, nice to see you" is triggered by InitilizedEvent, which is triggered by interface after Loading success

                    env.say(file('computer'))
                    env.wait_for(
                        lambda z: isinstance(z, StatefulRecorderStateEvent) and z.state == StatefulRecorderState.Open)

                    env.say(file('are_you_here'))
                    env.parse_reaction(TextCommand)

                    env.say(file('computer'))
                    env.wait_for(
                        lambda z: isinstance(z, StatefulRecorderStateEvent) and z.state == StatefulRecorderState.Open)

                    env.say(file('repeat_after_me'))
                    env.parse_reaction(TextCommand)
                    env.wait_for(
                        lambda z: isinstance(z, StatefulRecorderStateEvent) and z.state == StatefulRecorderState.Open)

                    env.say(file('make_me_a_sandwich'))
                    env.parse_reaction(TextCommand)
                finally:
                    pass

    def test_page_restart_on_server_restart(self):
        with BackendTestEnvironmentFactory(self, html=HTML) as env:
            with FrontendTestEnvironmentFactory(env.base_url, headless=True) as driver:
                try:
                    env.client.wait_for_availability()
                    env.client.scroll_to_end()
                    env.parse_reaction(TextCommand)  # "Hello, nice to see you" is triggered by InitilizedEvent, which is triggered by interface after Loading success

                    env.client.push(ServerStartedEvent())
                    env.wait_for(lambda z: isinstance(z, InitializationEvent))


                finally:
                    pass




HTML = '''
<html><head><meta charset="UTF-8"></head><body>
<script type="module">
  import {
    AvatarClient, Dispatcher, FakeMicrophone, MicController,
    Recorder, StatefulRecorder, SilenceDetector, Automaton, AudioController,
    Message, Envelop, 
  } from '/frontend/scripts/index.js';
  import { WakeWordDetector } from '/frontend/scripts/wakeWordDetector.js';
  import { LoadingScreen } from '/frontend/scripts/loadingScreen.js';



  const client = new AvatarClient({ baseUrl: window.location.origin });
  const dispatcher = new Dispatcher(client);
  const input = new FakeMicrophone({ sampleRate: 22050, frameSize: 512, acceleration: 10, dispatcher, baseUrl: window.location.origin });
  const recorder = new Recorder({ startBufferLength: 1.0, normalBufferLength: 0.3, dispatcher, baseUrl: window.location.origin });
  const stateful = new StatefulRecorder({ recorder, dispatcher });
  const silence = new SilenceDetector({ timeBetweenReportsInSeconds: 1, reportingWindowSeconds: 0.05, silenceLevel: 0.01, dispatcher });
  const wake = new WakeWordDetector({ sampleRateOfTheModel: 16000, words: ['computer'], modelUrl: '/frontend/models/vosk-model-small-en-us-0.15.zip', dispatcher });
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