import pickle
import traceback
import flask
import os
from recognition import FaceEmbedder
from pathlib import Path
import subprocess
import traceback


class InsightFaceApp:
    def __init__(self, embedder: FaceEmbedder):
        self.embedder = embedder


    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/analyze', view_func=self.analyze, methods=['POST'])
        return app

    def index(self):
        return "OK"

    def analyze(self):
        try:
            file = flask.request.files['file']
            data = file.stream.read()
            embeddings = self.embedder.extract_embeddings(data)
            return flask.jsonify(embeddings)
        except:
            return traceback.format_exc(), 500

