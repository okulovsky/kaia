import flask
import shutil
import os
import pickle
import uuid
import traceback
from tagger.interrogators import interrogators
from pathlib import Path
from PIL import Image

class WD14Server:
    def __init__(self):
        self.interrogators = {}

    def __call__(self):
        app = flask.Flask(__name__)
        app.add_url_rule('/interrogate/<model>/<threshold>', view_func=self.interrogate, methods=['POST'])
        app.add_url_rule('/tags/<model>', view_func=self.tags, methods=['POST'])
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.run('0.0.0.0',8084)

    def index(self):
        return "WD14 is running"

    def _get_interrogator(self, model):
        if model not in self.interrogators:
            self.interrogators[model] = interrogators[model]
            self.interrogators[model].use_cpu()
            self.interrogators[model].load()
        return self.interrogators[model]

    def interrogate(self, model, threshold):
        try:
            threshold = float(threshold)
            file = flask.request.files['file']
            image = Image.open(file)
            interrogator = self._get_interrogator(model)
            result = interrogator.interrogate(image)
            result = result[1]
            output = {key: value for key, value in result.items() if value>=threshold}
            return flask.jsonify(output)
        except:
            return traceback.format_exc(), 500


    def tags(self, model):
        try:
            interrogator = self._get_interrogator(model)
            tags = list([row[1].to_dict() for row in interrogator.tags.iterrows()])
            return flask.jsonify(tags)
        except:
            return traceback.format_exc(), 500








