import time
from unittest import TestCase
from kaia_tests.test_kaia.test_audio_control.setup import *
from kaia.infra import Loc
from kaia.infra.app import KaiaApp
from kaia.kaia.audio_control.wav_streaming import WavStreamingTestApi, WavApiSettings, WavServerSettings
from kaia.kaia.audio_control import AudioControlServer, AudioControlAPI
from pathlib import Path
from kaia_tests.test_kaia.test_audio_control.kaia_test_app import KaiaTestService
from kaia.kaia.gui import KaiaGuiService, KaiaGuiApi
from pprint import pprint
import pandas as pd

def wait_for_chat(stage, api, messages_count, max_waiting_time):
    print(f'INPUT> {stage}')
    update = None
    for _ in range(max_waiting_time):
        update = api.updates()['chat']
        for message in update:
            if message['is_error']:
                raise ValueError(f"Erroneous message in chat:\n{message['text']}")
        if len(update) >= messages_count:
            pprint(update)
            return update
        time.sleep(1)
    pprint(update)
    raise ValueError(f"Couldn't get {messages_count} messages in {max_waiting_time} seconds")


class AudioControlServerTestCase(TestCase):
    def check(self, n, api: KaiaGuiApi):
        chat = api.updates()['chat']
        if len(chat) != n:
            pprint(chat)
        self.assertEqual(n, len(chat))



    def test_audio_control_server(self):

        with Loc.create_temp_folder('audio_control_bb_folder', dont_delete=True) as folder:
            with create_brainbox_test_api(folder) as bb_api:
                with WavStreamingTestApi(WavApiSettings(), WavServerSettings(folder)) as wav_api:
                    settings = create_audio_control_settings(wav_api.settings.address)

                    settings.load_mic_samples = [
                        Path(__file__).parent / 'files/computer.wav',
                        Path(__file__).parent / 'files/are_you_here.wav',
                        Path(__file__).parent / 'files/computer.wav',
                        Path(__file__).parent / 'files/repeat_after_me.wav',
                        Path(__file__).parent/'files/make_me_a_sandwich.wav'
                    ]


                    app = KaiaApp()
                    audio_server = AudioControlServer(settings.create_audio_control, settings.port)
                    app.add_subproc_service(audio_server)
                    audio_api = AudioControlAPI(f'127.0.0.1:{settings.port}')

                    kaia_gui = KaiaGuiService()
                    app.add_subproc_service(kaia_gui)
                    kaia_gui_api = KaiaGuiApi(f'127.0.0.1:{kaia_gui._port}')

                    kaia = KaiaTestService(bb_api, audio_api, kaia_gui_api)
                    app.add_subproc_service(kaia)

                    with app.test_runner():
                        try:
                            kaia.wait_for_availability()

                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()

                            wait_for_chat('are_you_here', kaia_gui_api, 4, 10)

                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()
                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()

                            wait_for_chat('repeat_after_me', kaia_gui_api, 6, 10)

                            audio_api.next_mic_sample()
                            audio_api.wait_for_mic_sample_to_finish()

                            wait_for_chat('sandwich', kaia_gui_api, 8, 10)

                        finally:
                            for task in bb_api.get_summary()[:10]:
                                print(task['id'], task['received_timestamp'], task['decider'])
                            df = audio_api.status()
                            pd.options.display.width = None
                            print(df)







'''
0   5.559426    Standby       Open    None    None                                     None
1   5.559426       Open       Open    None  + None                                     None
2   5.559426       Open       Open  + None    None                                     None
3   5.399404       Open  Recording    None    None                                     None
4   5.391405  Recording    Standby    None    None  id_3dd5e469f3794fd7b32ddeb631bfd2b8.wav
5   5.391405    Standby    Standby    None  + None                                     None
6   5.391405    Standby    Standby  + None    None                                     None
7   3.368599    Standby       Open    None    None                                     None
8   3.368599       Open       Open    None  + None                                     None
9   3.368599       Open       Open  + None    None                                     None
10  3.103581       Open  Recording    None    None                                     None
11  3.098582  Recording    Standby    None    None  id_21857bdb72cc464bb330a638f5187140.wav
12  3.097582    Standby    Standby    None  + None                                     None
13  3.097582    Standby    Standby  + None    None                                     None
14  2.618763    Standby       Open    None    None                                     None
15  2.618763       Open       Open    None  + None                                     None
16  2.618763       Open       Open  + None    None                                     None
17  2.035294       Open  Recording    None    None                                     None
18  2.028294  Recording    Standby    None    None  id_399eb5ef8773483b8c02d39ffc910fc5.wav
19  2.028294    Standby    Standby    None  + None                                     None
20  2.028294    Standby    Standby  + None    None                                     None
'''