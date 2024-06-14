import io
import flask
from uuid import uuid4
import os
import sys
from tts_loader import load_tts
import traceback

class CoquiInferenceWebApp:
    def create_app(self):
        app = flask.Flask("CoquiTTSWebApp")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/run_model', view_func=self.run_model, methods=['POST'])
        app.add_url_rule('/run_synthesizer', view_func=self.run_synthesizer, methods=['POST'])
        return app

    def index(self):
        return f"{type(self).__name__} is running"


    def load_model(self):
        try:
            model_name = flask.request.json['model']
            data = load_tts(model_name)
            self.tts = data.tts
            reply = dict(
                speakers=getattr(self.tts,'speakers', None),
                languages=getattr(self.tts,'languages', None),
                device=data.device,
                is_custom_model = data.is_custom_model
            )
            return flask.jsonify(reply)
        except:
            return traceback.format_exc(), 500


    def _send_as_file(self, fname):
        with open(fname, 'rb') as file:
            bytes = file.read()
        os.unlink(fname)
        bytes_io = io.BytesIO(bytes)
        return flask.send_file(
            bytes_io,
            mimetype='binary/octet-stream'
        )


    def run_model(self):
        try:
            kwargs = flask.request.json
            fname = f'output_{uuid4()}.wav'
            self.tts.tts_to_file(file_path=fname, **kwargs)
            return self._send_as_file(fname)
        except:
            return traceback.format_exc(), 500


    def run_synthesizer(self):
        try:
            kwargs = flask.request.json
            wav = self.tts.synthesizer.tts(**kwargs)
            fname = f'output_{uuid4()}.wav'
            self.tts.synthesizer.save_wav(wav=wav,path=fname,pipe_out=None)
            return self._send_as_file(fname)
        except:
            return traceback.format_exc(), 500