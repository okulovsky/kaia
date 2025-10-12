import subprocess
import traceback
import flask
import os
import wave
import json
from vosk import Model, KaldiRecognizer, SetLogLevel
from uuid import uuid4

class VoskApp:
    def __init__(self):
        self.model = None
        self.model_name = None

    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/transcribe', view_func=self.transcribe, methods=['POST'])
        app.add_url_rule('/transcribe/<model_name>', view_func=self.transcribe, methods = ['POST'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/get_loaded_model', view_func=self.get_loaded_model, methods=['GET'])
        return app

    def index(self):
        return "OK"


    def _load_model_internal(self, model_name):
        self.model = Model('/models/'+model_name)
        self.model_name = model_name
        return 'OK'

    def load_model(self):
        try:
            model_name = flask.request.json['model']
            return self._load_model_internal(model_name)
        except:
            return traceback.format_exc(), 500

    def get_loaded_model(self):
        return flask.jsonify(self.model_name)


    def transcribe(self, model_name = None):
        fname = f'/resources/input_{uuid4()}.wav'
        try:
            if model_name is None:
                if self.model_name is None:
                    raise ValueError("No model is provided with a request and no model is pre-loaded on the server")
            else:
                if self.model_name is None or self.model_name != model_name:
                    self._load_model_internal(model_name)

            file = flask.request.files['file']
            file.save(fname)
            try:
                wf = wave.open(fname, "rb")
            except:
                fixed_fname = f'/resources/input_{uuid4()}.wav'
                subprocess.call(['ffmpeg','-i',fname,fixed_fname])
                os.unlink(fname)
                fname = fixed_fname
                wf = wave.open(fname, "rb")

            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                raise ValueError("Audio file must be WAV format mono PCM.")
            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            results = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    results.append(part_result)

            part_result = json.loads(rec.FinalResult())
            results.append(part_result)

            return flask.jsonify(results)
        except:
            return traceback.format_exc(), 500
        finally:
            os.unlink(fname)