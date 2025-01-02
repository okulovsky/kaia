import os

import flask
import subprocess
from pathlib import Path
from kaia.common import Loc
from uuid import uuid4

class PlayServer:
    def create_app(self):
        app = flask.Flask('audio_server')
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/play', view_func=self.play, methods=['POST'])
        app.add_url_rule('/volume', view_func=self.volume, methods=['POST'])
        app.add_url_rule('/test', view_func=self.test, methods=['GET'])
        return app

    def __call__(self):
        app = self.create_app()
        app.run('0.0.0.0', 13001)


    def index(self):
        return 'Play server is running'

    def _play(self, path):
        subprocess.call(['play', path])


    def test(self):
        self._play(Path(__file__).parent/'beep.wav')
        return 'ok'

    def play(self):
        fname = Loc.data_folder/f'{uuid4()}.wav'
        with open(fname, 'wb') as file:
            file.write(flask.request.data)
        self._play(fname)
        os.unlink(fname)
        return 'ok'

    def volume(self):
        volume = flask.request.json['volume']
        value = int(volume * 100)
        subprocess.call(['amixer', '-D', 'pulse', 'sset', 'Master', f'{value}%'])
        return 'ok'



