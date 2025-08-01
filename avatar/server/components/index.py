import flask
import time
from datetime import datetime
from pathlib import Path
import os
import wave
from .avatar_component import IAvatarComponent
import struct
from dataclasses import dataclass

@dataclass
class IndexComponent(IAvatarComponent):
    text: str|None = None
    base_url: str|None = None

    def setup_server(self, app: flask.Flask):
        app.add_url_rule('/', view_func=self.index, methods=['GET'])

    def index(self):
        if self.text is None:
            return 'OK'
        text = self.text
        if self.base_url is not None:
            text = text.replace('#base_url', self.base_url)
        return text
