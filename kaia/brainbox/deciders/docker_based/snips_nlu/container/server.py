import os
import sys
import traceback
import subprocess
import yaml
from uuid import uuid4
import json
from pathlib import Path

import flask
from snips_nlu import SnipsNLUEngine

class SnipsNLUWebApp:
    def create_app(self):
        self.engines = {}
        self.data_path = Path('/data')
        os.makedirs(self.data_path, exist_ok=True)
        app = flask.Flask("snips_nlu")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/train', view_func=self.train, methods=['POST'])
        app.add_url_rule('/parse', view_func=self.parse, methods=['POST'])
        return app

    def index(self):
        return 'SnipsNLU is working<br>Models: '+', '.join(self.engines)

    def train(self):
        try:
            rq = flask.request.json
            data = rq['data']
            fname = self.data_path/f'{uuid4()}.yaml'
            with open(fname,'w') as file:
                yaml.dump_all(data, file)
            try:
                js = subprocess.check_output(['snips-nlu','generate-dataset','en', fname])
            except subprocess.CalledProcessError as ex:
                return f'Dataset convertor failed with output\n{ex.output}', 500

            os.unlink(fname)
            data = json.loads(js)

            engine = SnipsNLUEngine()
            engine.fit(data)
            self.engines[rq['profile']] = engine
            return 'OK'
        except:
            return traceback.format_exc(), 500

    def parse(self):
        try:
            data = flask.request.json
            return flask.jsonify(self.engines[data['profile']].parse(data['text']))
        except:
            return traceback.format_exc(), 500



