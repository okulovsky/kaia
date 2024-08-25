import time
from unittest import TestCase
from pathlib import Path

import pandas as pd

from my.demo.main import create_app
from pprint import pprint
from kaia.brainbox.deciders import WhisperInstaller, RhasspyInstaller, WhisperSettings, RhasspySettings

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

class DemoTestCase(TestCase):
    def test_demo(self):
        WhisperInstaller(WhisperSettings()).run_in_any_case_and_create_api()
        RhasspyInstaller(RhasspySettings()).run_in_any_case_and_create_api()

        samples = [
            Path(__file__).parent/'test_audio_control/files/computer.wav',
            Path(__file__).parent/'test_audio_control/files/are_you_here.wav',
            Path(__file__).parent/'test_audio_control/files/computer.wav',
            Path(__file__).parent/'test_audio_control/files/repeat_after_me.wav',
            Path(__file__).parent/'test_audio_control/files/make_me_a_sandwich.wav',
        ]
        app = create_app(samples, False)
        with app.app.test_runner():
            try:
                wait_for_chat('init', app.gui_api, 3, 60)

                app.audio_api.next_mic_sample()
                app.audio_api.wait_for_mic_sample_to_finish()
                app.audio_api.next_mic_sample()
                app.audio_api.wait_for_mic_sample_to_finish()

                wait_for_chat('are you here?', app.gui_api, 5, 30)

                app.audio_api.next_mic_sample()
                app.audio_api.wait_for_mic_sample_to_finish()
                app.audio_api.next_mic_sample()
                app.audio_api.wait_for_mic_sample_to_finish()

                wait_for_chat('repeat after me', app.gui_api, 7, 30)

                app.audio_api.next_mic_sample()
                app.audio_api.wait_for_mic_sample_to_finish()

                final_chat = wait_for_chat('repetition', app.gui_api, 9, 30)

                print(f'OUTPUT CHAT\n\n{final_chat}')

                texts = [z['text'] for z in final_chat]

                self.assertEqual(9, len(texts))
                self.assertListEqual(
                    [
                        'Rhasspy is training', 'Rhasspy has been trained', 'Hello! Nice to see you!',
                        'Are you here?', "Sure, I'm listening.", 'Repeat after me!', 'Say anything and I will repeat.',
                     ],
                    texts[:7]
                )
                self.assertEqual(texts[-2].lower(), texts[-1].lower())

            finally:
                for task in reversed(app.brainbox_api.get_summary()[-10:]):
                    print(task['id'], task['received_timestamp'], task['decider'])

                df = app.audio_api.status()
                pd.options.display.width = None
                print(df)





