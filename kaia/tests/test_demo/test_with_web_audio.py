from unittest import TestCase
from kaia.common import Loc
from kaia.demo import *
from brainbox.framework import Fork



cmd = '''
source ~/.nvm/nvm.sh && \
nvm use 20.19.0 && \
OPEN=false npm run dev
'''

class WithAudioTestCase(TestCase):
    def test_with_web_audio(self):
        with Loc.create_test_folder() as folder:
            app = KaiaApp(folder, 'test')
            set_brainbox_service_and_api(app)
            set_streaming_service_and_api_address(app)
            set_avatar_service_and_api(app)
            set_web_service_and_api(app)


            set_core_service(app)

            with KaiaAppTester(app, self) as tester:
                updates = tester.pull_updates(3, 10)
                print(updates)

                with Frontend('20.19.0', Loc.root_folder / '0-latency-voice-uploader'):
                    with Frontend.BrowserInstance(False):
                        updates = tester.pull_updates(7, 15)

                        #tester.send_voice_command_via_mocked_web_mic("Computer!")

                        updates = tester.pull_updates(2, 600, 'UPDATE: ')




