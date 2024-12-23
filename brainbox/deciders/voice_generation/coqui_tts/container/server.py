import io
import flask
from tts_loader import load_tts
import traceback
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModelInfo:
    name: str
    speakers: list[str]|None
    languages: list[str]|None
    device: str
    is_custom_model: bool


class CoquiInferenceWebApp:
    def __init__(self):
        self.tts = None
        self.model: ModelInfo|None = None


    def create_app(self):
        app = flask.Flask("CoquiTTSWebApp")
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/load_model', view_func=self.load_model, methods=['POST'])
        app.add_url_rule('/dub', view_func=self.dub, methods=['POST'])
        app.add_url_rule('/voice_clone', view_func=self.voice_clone, methods=['POST'])

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    def _load_model_internal(self, model_name):
        if model_name is None:
            if self.model is None:
                raise ValueError("No model is pre-loaded and no model is specified in the request")
            else:
                return
        if self.model is not None:
            if self.model.name == model_name:
                return
        data = load_tts(model_name)
        self.tts = data.tts

        self.model = ModelInfo(
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
            return flask.jsonify(self.model.__dict__)
        except:
            return traceback.format_exc(), 500


    def _get_language(self, language) -> str|None:
        if language is None and self.model.languages is not None:
            language = self.model.languages[0]
        if language is not None and self.model.languages is None:
            language = None
        return language

    def _send_as_file(self, buffer):
        return flask.send_file(
            buffer,
            mimetype='binary/octet-stream'
        )

    def _run_model(self, **kwargs):
        buffer = io.BytesIO()
        self.tts.tts_to_file(file_path=buffer, **kwargs)
        return self._send_as_file(buffer)

    def _run_synthesizer(self, **kwargs):
        buffer = io.BytesIO()
        wav = self.tts.synthesizer.tts(**kwargs)
        self.tts.synthesizer.save_wav(wav=wav, path=buffer, pipe_out=None)
        return self._send_as_file(buffer)

    def dub(self):
        try:
            model = flask.request.json['model']
            self._load_model_internal(model)
            text = flask.request.json['text']
            voice = flask.request.json['voice']
            language = flask.request.json['language']

            language = self._get_language(language)
            if voice is None and self.model.speakers is not None:
                voice = self.model.speakers[0]

            return self._run_synthesizer(text=text, speaker_name=voice, language_name=language)
        except:
            return traceback.format_exc(), 500

    def voice_clone(self):
        try:
            model = flask.request.json['model']
            self._load_model_internal(model)
            text = flask.request.json['text']
            voice = flask.request.json['voice']
            language = flask.request.json['language']
            language = self._get_language(language)
            path = f'/resources/voices/{voice}.wav'
            if not Path(path).is_file():
                raise ValueError(f"File {path} not found, perhaps the voice sample was not uploaded")
            return self._run_model(text=text, speaker_wav=path, language=language)
        except:
            return traceback.format_exc(), 500


