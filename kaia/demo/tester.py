import time

import requests
from kaia.avatar.utils import TestSpeaker
from .app import KaiaApp
from brainbox.framework.common import ApiUtils
from unittest import TestCase
from kaia.kaia import BusItem
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint

@dataclass
class BusItemWrapper:
    item: BusItem
    tc: TestCase

    def of_type(self, type: str):
        self.tc.assertEqual(type, self.item.type)

    def _validate_message(self, message_type: str, subs: str|None, sender: str|None):
        self.tc.assertTrue('reaction_message', self.item.type)
        self.tc.assertEqual(message_type, self.item.payload['type'])
        if subs is not None:
            self.tc.assertIn(subs, self.item.payload['text'])
        if sender is not None:
            self.tc.assertEqual(sender, self.item.payload['sender'])



    def is_system_message(self, subs: str|None = None):
        self._validate_message('System', subs, None)

    def is_bot_message(self, subs: str|None = None, sender: str|None = None):
        self._validate_message('ToUser', subs, sender)

    def is_user_message(self, subs: str|None = None):
        self._validate_message('FromUser', subs, None)

    def _get_metadata(self) -> dict:
        if self.item.payload['metadata'] is None:
            raise ValueError("Metadata is not set")
        if not isinstance(self.item.payload['metadata'], dict):
            raise ValueError(f"Metadata is expected to be dict, but was: {self.item.payload['metadata']}")
        return self.item.payload['metadata']

    def is_bot_audio(self, subs: str|None = None, speaker: str|None = None):
        self.tc.assertEqual('reaction_audio', self.item.type)
        if subs is not None:
            self.tc.assertIn(subs, self._get_metadata()['text'])
        if speaker is not None:
            self.tc.assertEqual(speaker, self._get_metadata()['speaker'])


    def is_image(self, character: str | None = None):
        self.tc.assertEqual('reaction_image', self.item.type)
        if character is not None:
            self.tc.assertEqual(character, self._get_metadata()['tags']['character'])





class KaiaAppTester:
    def __init__(self, app: KaiaApp, tc: TestCase):
        self.app = app
        self.test_speaker = TestSpeaker(self.app.brainbox_api)
        self.tc = tc

    def __enter__(self):
        self.fork_app = self.app.get_fork_app(True)
        self.fork_app.run()
        ApiUtils.wait_for_reply(self.endpoint(), 5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fork_app.terminate()

    def endpoint(self, endpoint: str|None = None):
        result = f"http://127.0.0.1:{self.app.kaia_server.settings.port}"
        if endpoint is not None:
            result+=endpoint
        return result




    def send_voice_command(self, text: str, speaker: int|str|None = None):
        file_id = self.test_speaker.speak(text, speaker)
        requests.post(
            self.endpoint(f'/command/{self.app.session_id}/command_audio'),
            json=file_id
        )

    def send_voice_command_via_audio_control(self, text: str, speaker: int|str|None = None):
        path = self.test_speaker.speak(text, speaker, return_cache_path=True)
        self.app.audio_control_api.playback_mic_sample(path)

    def send_initial_package(self):
        return requests.post(
            self.endpoint(f'/command/{self.app.session_id}/command_initialize'),
            json=''
        ).json()

    def send_sound_confirmation(self, update: 'BusItemWrapper'):
        requests.post(
            self.endpoint(f'/command/{self.app.session_id}/confirmation_audio'),
            json=update.item.payload['filename']
        )

    def pull_updates(self, count: int|None = None, time_limit_in_seconds: int = 10) -> list[BusItemWrapper]:
        start = datetime.now()
        result = []
        while True:
            for c in self.app.kaia_api.pull_updates():
                result.append(BusItemWrapper(c, self.tc))
            if count is not None:
                if len(result) == count:
                    return result
                if len(result) > count:
                    pprint(result)
                    self.tc.fail(f"Expected {count} updates, but was {len(result)}")
            if (datetime.now() - start).total_seconds() > time_limit_in_seconds:
                pprint(result)
                raise ValueError(f"Time limit exceeded. {len(result)} updates were collected")
            time.sleep(0.1)

    def pull_updates_via_html(self, last_message_id: int, count: int|None = None, time_limit_in_seconds: int = 10) -> list:
        start = datetime.now()
        while True:
            updates = requests.get(self.endpoint(f'/updates/{self.app.session_id}/{last_message_id}')).json()
            result = [BusItemWrapper(BusItem(**u), self.tc) for u in updates]
            if count is not None:
                if len(result) == count:
                    return result
                if len(result) > count:
                    self.tc.fail(f"Expected {count} updates, but was {len(result)}")
            if (datetime.now() - start).total_seconds() > time_limit_in_seconds:
                pprint(result)
                raise ValueError(f"Time limit exceeded. {len(result)} updates were collected")
            time.sleep(0.1)



