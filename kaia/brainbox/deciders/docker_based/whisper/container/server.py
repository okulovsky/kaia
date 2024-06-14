import flask
from uuid import uuid4
import traceback
import whisper
import uuid
import os

class WhisperApp:
    def __init__(self):
        self.model = None

    def create_app(self):
        app = flask.Flask("Whisper STT Web App")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/transcribe', view_func=self.transcribe, methods=['POST'])
        return app

    def index(self):
        return f"{type(self).__name__} is running"


    def load_model(self):
        try:
            model_name = flask.request.json['model']
            self.model = whisper.load_model(model_name, download_root='/data/')
            return 'OK'
        except:
            return traceback.format_exc(), 500


    def transcribe(self):
        try:
            fname = f'/data/input_{uuid4()}.wav'
            file = flask.request.files['file']
            file.save(fname)
            result = self.model.transcribe(fname)
            return flask.jsonify(result)
        except:
            return traceback.format_exc(), 500

