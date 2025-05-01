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
    def __init__(self,
                 app: KaiaApp,
                 tc: TestCase,
                 custom_brainbox_api = None,
                 custom_kaia_address = None,
                 custom_session_id = None,
                 ):
        self.app = app
        self.tc = tc

        if custom_brainbox_api is None:
            self.test_speaker = TestSpeaker(self.app.brainbox_api, copy_to_folder=self.app.folder/'kaia/cache')
        else:
            self.test_speaker = TestSpeaker(custom_brainbox_api, copy_to_folder=self.app.folder/'kaia/cache')
        if custom_kaia_address is None:
            self.address = f"127.0.0.1:{self.app.kaia_server.settings.port}"
        else:
            self.address = custom_kaia_address
        if custom_session_id is None:
            self.session_id = self.app.session_id
        else:
            self.session_id = custom_session_id

    def __enter__(self):
        self.fork_app = self.app.get_fork_app(True)
        self.fork_app.run()
        ApiUtils.wait_for_reply(self.endpoint(), 20)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fork_app.terminate()

    def endpoint(self, endpoint: str|None = None):
        result = 'http://'+self.address
        if endpoint is not None:
            result+=endpoint
        return result




    def send_voice_command(self, text: str, speaker: int|str|None = None):
        file_id = self.test_speaker.speak(text, speaker)
        requests.post(
            self.endpoint(f'/command/{self.session_id}/command_audio'),
            json=file_id
        )

    def send_voice_command_via_audio_control(self, text: str, speaker: int|str|None = None):
        path = self.test_speaker.speak(text, speaker, return_cache_path=True)
        self.app.audio_control_api.playback_mic_sample(path)

    def send_voice_command_via_mocked_web_mic(self, text, speaker: int|str|None = None):
        name = self.test_speaker.speak(text, speaker, False)
        requests.post(
            self.endpoint(f'/command/{self.session_id}/injection_audio'),
            json = dict(filename=name)
        )

    def send_initial_package(self):
        return requests.post(
            self.endpoint(f'/command/{self.session_id}/command_initialize'),
            json=''
        ).json()

    def send_sound_confirmation(self, update: 'BusItemWrapper'):
        requests.post(
            self.endpoint(f'/command/{self.session_id}/confirmation_audio'),
            json=update.item.payload['filename']
        )

    def pull_updates(self, count: int|None = None, time_limit_in_seconds: int = 10, print_every_and_use_prefix: str|None = None) -> list[BusItemWrapper]:
        start = datetime.now()
        result = []
        while True:
            for c in self.app.kaia_api.pull_updates():
                result.append(BusItemWrapper(c, self.tc))
                if print_every_and_use_prefix is not None:
                    print(f'{print_every_and_use_prefix}{c}')
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

    def pull_updates_via_html(self, last_message_id: int, count: int|None = None, time_limit_in_seconds: int = 10) -> list[BusItemWrapper]:
        start = datetime.now()
        while True:
            updates = requests.get(self.endpoint(f'/updates/{self.session_id}/{last_message_id}')).json()
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

    def get_available_updates_via_html(self) -> list[BusItemWrapper]:
        updates = requests.get(self.endpoint(f'/updates/{self.session_id}/0')).json()
        result = [BusItemWrapper(BusItem(**u), self.tc) for u in updates]
        return result



