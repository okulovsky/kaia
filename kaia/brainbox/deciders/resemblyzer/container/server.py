import traceback

import flask
from pathlib import Path
import shutil
import os
import pickle
import uuid
import traceback

import pandas as pd

from classifier import *

DATASETS_PATH = Path('/data/datasets')
MODELS_FOLDER = Path('/data/models')

class ResemblyzerServer:
    def __init__(self):
        self.wav_processor = WavProcessor()
        self.models_cache: dict[str, Model] = {}


    def __call__(self):
        app = flask.Flask(__name__)
        app.add_url_rule('/delete_dataset/<model>', view_func=self.delete_dataset, methods=['POST'])
        app.add_url_rule('/upload_dataset_file/<model>/<split>/<speaker>/<file>', view_func=self.upload_dataset_file, methods=['POST'])
        app.add_url_rule('/train/<model>', view_func=self.train, methods=['POST'])
        app.add_url_rule('/classify/<model>', view_func=self.classify, methods=['POST'])
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.run('0.0.0.0',8084)

    def index(self):
        return 'OK'


    def upload_dataset_file(self, model, split, speaker, file):
        path = DATASETS_PATH/model/split/speaker/file
        os.makedirs(path.parent, exist_ok=True)
        file = flask.request.files['file']
        file.save(path)
        return 'OK'

    def delete_dataset(self, model):
        shutil.rmtree(DATASETS_PATH/model, ignore_errors=True)
        return 'OK'

    def train(self, model: str):
        try:
            train = self.wav_processor.get_encodings(DATASETS_PATH/model/'train')
            model_instance = Model(train)

            test = self.wav_processor.get_encodings(DATASETS_PATH/model/'test')
            model_instance.evaluate(test)

            os.makedirs(MODELS_FOLDER, exist_ok=True)
            with open(MODELS_FOLDER/model,'wb') as file:
                pickle.dump(model_instance.__dict__, file)
            stats_df = {column: list(model_instance.stats[column]) for column in model_instance.stats}
            return flask.jsonify(dict(accuracy=model_instance.accuracy, stats = stats_df))
        except:
            return traceback.format_exc(), 500

    def classify(self, model: str):
        try:
            path = Path('/data')/str(uuid.uuid4())
            file = flask.request.files['file']
            file.save(path)
            embedding = self.wav_processor.get_encoding(path)
            os.unlink(path)
            if model not in self.models_cache:
                with open(MODELS_FOLDER/model,'rb') as file:
                    self.models_cache[model] = Model(**pickle.load(file))
            winner = self.models_cache[model].compute_winner(embedding)
            if winner is None:
                raise ValueError("Undef winner")
            return flask.jsonify(dict(speaker=winner))
        except:
            return traceback.format_exc(), 500










