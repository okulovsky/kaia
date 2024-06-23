import time
from unittest import TestCase
from pathlib import Path
from my.demo.main import create_app
from pprint import pprint

def wait_for_chat(stage, api, messages_count, max_waiting_time):
    print(stage)
    for _ in range(max_waiting_time):
        update = api.updates()
        if len(update['chat']) >= messages_count:
            pprint(update['chat'])
            return
        time.sleep(1)
    raise ValueError(f"Couldn't get {messages_count} messages in {max_waiting_time} seconds")

class DemoTestCase(TestCase):
    def test_demo(self):
        samples = [
            Path(__file__).parent/'test_audio_control/files/computer.wav',
            Path(__file__).parent/'test_audio_control/files/are_you_here.wav',
            Path(__file__).parent/'test_audio_control/files/computer.wav',
            Path(__file__).parent/'test_audio_control/files/repeat_after_me.wav',
            Path(__file__).parent/'test_audio_control/files/random_text_outside_of_intents.wav'
        ]
        app = create_app(samples, False)
        with app.app.test_runner():
            wait_for_chat('init', app.gui_api, 3, 60)

            app.audio_api.next_mic_sample()
            app.audio_api.wait_for_mic_sample_to_finish()
            app.audio_api.next_mic_sample()
            app.audio_api.wait_for_mic_sample_to_finish()

            wait_for_chat('are you here?', app.gui_api, 5, 10)

            app.audio_api.next_mic_sample()
            app.audio_api.wait_for_mic_sample_to_finish()
            app.audio_api.next_mic_sample()
            app.audio_api.wait_for_mic_sample_to_finish()

            wait_for_chat('repeat after me', app.gui_api, 7, 10)

            app.audio_api.next_mic_sample()
            app.audio_api.wait_for_mic_sample_to_finish()

            wait_for_chat('repetition', app.gui_api, 9, 10)
