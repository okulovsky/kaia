import os

import flask
from uuid import uuid4
import traceback
import whisper
import json
from io import BytesIO

class WhisperApp:
    def __init__(self):
        self.model = None
        self.model_name = None


    def create_app(self):
        app = flask.Flask("Whisper STT Web App")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/get_loaded_model', view_func=self.get_loaded_model, methods=['GET'])
        app.add_url_rule('/transcribe', view_func=self.transcribe, methods=['POST'])

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    def _load_model_internal(self, model_name):
        self.model = whisper.load_model(model_name, download_root='/resources/')
        self.model_name = model_name
        return 'OK'

    def load_model(self):
        try:
            model_name = flask.request.json['model']
            return self._load_model_internal(model_name)
        except:
            return traceback.format_exc(), 500

    def get_loaded_model(self):
        return flask.jsonify(dict(name=self.model_name))


    def transcribe(self):
        fname = f'/resources/input_{uuid4()}.wav'
        try:
            file = flask.request.files['file']
            file.save(fname)

            param_file = flask.request.files['parameters']
            param_str = param_file.stream.read()
            params = json.loads(param_str)

            model = params['model']
            if model is None:
                if self.model_name is None:
                    raise ValueError("No model is provided with a request and no model is pre-loaded on the server")
            else:
                if self.model_name is None or self.model_name != model:
                    self._load_model_internal(model)
            result = self.model.transcribe(fname, **params['parameters'])
            return flask.jsonify(result)
        except:
            return traceback.format_exc(), 500
        finally:
            os.unlink(fname)

