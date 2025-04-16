import traceback

import flask
from pathlib import Path
import shutil
import os
import pickle
import uuid
import traceback
from model import Model, Transcriber
from utils import profile_path

DATASETS_PATH = Path('/data/datasets')
MODELS_FOLDER = Path('/data/models')

class RhasspyKaldiServer:
    def __init__(self):
        self.transcribers: dict[str, Transcriber] = {}

    def __call__(self):
        app = flask.Flask(__name__)
        app.add_url_rule('/train/<language>/<model>', view_func=self.train, methods=['POST'])
        app.add_url_rule('/transcribe/<model>', view_func=self.transcribe, methods=['POST'])
        app.add_url_rule('/phonemes/<language>', view_func=self.phonemes, methods=['GET'])
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.run('0.0.0.0',8084)

    def index(self):
        return 'OK'

    def transcribe(self, model):
        try:
            file = flask.request.files['file']
            content = file.stream.read()
            if model not in self.transcribers:
                self.transcribers[model] = Model(model).create_transcriber()
            return flask.jsonify(self.transcribers[model].transcribe(content))
        except:
            return traceback.format_exc(), 500


    def train(self, language, model):
        try:
            js = flask.request.json
            sentences = js['sentences']
            custom_words = js['custom_words']
            model_object = Model(model)
            result = model_object.train(language, sentences, custom_words)
            self.transcribers[model] = model_object.create_transcriber()
            return flask.jsonify(result)
        except:
            return traceback.format_exc(), 500

    def phonemes(self, language):
        with open(profile_path/language/'kaldi/phoneme_examples.txt') as file:
            return file.read()







