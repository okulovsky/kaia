import traceback

import flask
import time
from datetime import datetime
from pathlib import Path
import os
import wave
from .avatar_component import IAvatarComponent, AvatarApp
import struct
from dataclasses import dataclass

@dataclass
class MainComponent(IAvatarComponent):
    text: str|None = None
    base_url: str|None = None

    def setup_server(self, app: AvatarApp, address: str):
        if self.base_url is None:
            self.base_url = address
        app.add_url_rule('/main', view_func=self.main, methods=['GET'], caption="Main page")

    def main(self):
        text = self.text
        if self.base_url is not None:
            text = text.replace('#base_url', self.base_url)
        return text
