import os
import traceback
import uuid
from converter import Converter
import traceback
from pathlib import Path
import pickle
from pydantic import BaseModel
import flask


OUTPUT_DIR = '/home/app/outputs'


class Server:
    def __init__(self):
        self.converter = Converter()
        self.loaded_models = {}

    def __call__(self):
        app = flask.Flask("OpenVoiceServer")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/train/<model>', view_func=self.train, methods=['POST'])
        app.add_url_rule('/generate/<model>', view_func=self.generate, methods=['POST'])
        app.add_url_rule('/generate/<model>/<source_model>', view_func=self.generate, methods=['POST'])
        app.run('0.0.0.0', port=8080)



    def index(self):
        return "OK"

    def train(self, model: str):
        try:
            from train import train
            train(model, self.converter)
            return "OK"
        except:
            result = traceback.format_exc()
            return result, 500

    def _get_model(self, model):
        if model not in self.loaded_models:
            model_path = Path(f'/models/{model}')
            if not model_path.is_file():
                raise ValueError(f"Model {model} was not trained")
            with open(f'/models/{model}', 'rb') as stream:
                self.loaded_models[model] = pickle.load(stream)
        return self.loaded_models[model]

    def generate(self, model, source_model=None):
        source_path = None
        output_path = None
        try:
            id = uuid.uuid4()
            output_path = f"{OUTPUT_DIR}/output_{id}.wav"
            source_path = f"{OUTPUT_DIR}/source_{id}.wav"

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            file = flask.request.files['file']
            file.save(source_path)

            target_se = self._get_model(model)
            if source_model is not None:
                source_se = self._get_model(source_model)
            else:
                source_se = self.converter.convert(source_path)

            encode_message = "@MyShell"

            self.converter.tone_color_converter.convert(
                audio_src_path=source_path,
                src_se=source_se,
                tgt_se=target_se,
                output_path=output_path,
                message=encode_message
            )

            if not os.path.exists(output_path):
                raise ValueError("OpenVoice failed to create an output file")

            return flask.send_file(output_path)
        except:
            return traceback.format_exc(), 500
        finally:
            for path in [source_path, output_path]:
                if path is not None and os.path.exists(path):
                    os.remove(path)
