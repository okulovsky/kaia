import io
import flask
from uuid import uuid4
import os
from tts_loader import load_tts
import traceback
from pathlib import Path
import subprocess

class CoquiInferenceWebApp:
    def __init__(self, autoload_model: None|str):
        self.tts = None
        self.model = None
        self.autoload_model = autoload_model

    def create_app(self):
        app = flask.Flask("CoquiTTSWebApp")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/run_model', view_func=self.run_model, methods=['POST'])
        app.add_url_rule('/run_synthesizer', view_func=self.run_synthesizer, methods=['POST'])
        app.add_url_rule('/get_loaded_model', view_func=self.get_loaded_model, methods=['GET'])

        if self.autoload_model is not None:
            self._load_model_internal(self.autoload_model)

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    def _load_model_internal(self, model_name):
        data = load_tts(model_name)
        self.tts = data.tts
        self.model = dict(
            name=model_name,
            speakers=getattr(self.tts, 'speakers', None),
            languages=getattr(self.tts, 'languages', None),
            device=data.device,
            is_custom_model=data.is_custom_model
        )

    def load_model(self):
        try:
            model_name = flask.request.json['model']
            self._load_model_internal(model_name)
            return flask.jsonify(self.model)
        except:
            return traceback.format_exc(), 500

    def get_loaded_model(self):
        try:
            return flask.jsonify(self.model)
        except:
            return traceback.format_exc(), 500


    def _send_as_file(self, buffer):
        return flask.send_file(
            buffer,
            mimetype='binary/octet-stream'
        )



    def run_model(self):
        try:
            buffer = io.BytesIO()
            kwargs = flask.request.json
            self.tts.tts_to_file(file_path=buffer, **kwargs)
            return self._send_as_file(buffer)
        except:
            return traceback.format_exc(), 500


    def run_synthesizer(self):
        try:
            buffer = io.BytesIO()
            kwargs = flask.request.json
            print(kwargs)
            wav = self.tts.synthesizer.tts(**kwargs)
            self.tts.synthesizer.save_wav(wav=wav,path=buffer,pipe_out=None)
            return self._send_as_file(buffer)
        except:
            return traceback.format_exc(), 500
