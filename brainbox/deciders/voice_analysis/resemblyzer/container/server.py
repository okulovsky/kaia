import flask
import shutil
import os
import pickle
import uuid
import traceback

from classifier import *

DATASETS_PATH = Path('/resources/datasets')
MODELS_FOLDER = Path('/resources/models')

class ResemblyzerServer:
    def __init__(self):
        self.wav_processor = WavProcessor()
        self.models_cache: dict[str, Model] = {}


    def __call__(self):
        app = flask.Flask(__name__)
        app.add_url_rule('/train/<model>', view_func=self.train, methods=['POST'])
        app.add_url_rule('/classify/<model>', view_func=self.classify, methods=['POST'])
        app.add_url_rule('/distances/<model>', view_func=self.distances, methods=['POST'])
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.run('0.0.0.0',8084)

    def _get_model(self, model):
        if model not in self.models_cache:
            with open(MODELS_FOLDER / model, 'rb') as file:
                self.models_cache[model] = Model(**pickle.load(file))
        return self.models_cache[model]

    def _get_embedding(self):
        path = Path('/resources') / str(uuid.uuid4())
        file = flask.request.files['file']
        file.save(path)
        embedding = self.wav_processor.get_encoding(path)
        os.unlink(path)
        return embedding

    def classify(self, model: str):
        try:
            embedding = self._get_embedding()
            winner = self._get_model(model).compute_winner(embedding)
            if winner is None:
                raise ValueError("Undef winner")
            return flask.jsonify(dict(speaker=winner))
        except:
            return traceback.format_exc(), 500

    def distances(self, model: str):
        try:
            embedding = self._get_embedding()
            result = self._get_model(model).compute_full(embedding)
            return flask.jsonify(result)
        except:
            return traceback.format_exc(), 500

    def index(self):
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
            stats_df = model_instance.stats
            if stats_df is not None:
                stats_df = {column: list(model_instance.stats[column]) for column in stats_df}
            return flask.jsonify(dict(accuracy=model_instance.accuracy, stats = stats_df))
        except:
            return traceback.format_exc(), 500












