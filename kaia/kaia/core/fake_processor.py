import requests
import time
from .kaia_server import KaiaApi
from .kaia_message import KaiaMessage


class FakeKaiaProcess:
    def __init__(self,
                 api: KaiaApi
                 ):
        self.api = api
        self.actions = []

    def msg(self, is_bot, text):
        self.actions.append(dict(method='add_message', argument=KaiaMessage(is_bot, text)))
        return self

    def __call__(self):
        for action in self.actions:
            time.sleep(1)
            method = getattr(self.api, action['method'])
            method(action['argument'])
        while True:
            time.sleep(1)
