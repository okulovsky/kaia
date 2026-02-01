import traceback
import flask
import os
import uuid
from pathlib import Path
import io
import torchaudio
import json



class CosyVoiceApp:
    def __init__(self, model):
        self.model = model
        self.voices_folder = Path('/voices')
        self.speakers_folder = Path('/speakers')
        self.speakers_cache = {}

    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/heartbeat', view_func=self.heartbeat, methods=['GET'])
        app.add_url_rule('/train', view_func=self.train, methods=['POST'])
        app.add_url_rule('/voice_to_file', view_func=self.voice_to_file, methods=['POST'])
        app.add_url_rule('/voice_to_text', view_func=self.voice_to_text, methods=['POST'])
        app.add_url_rule('/voice_to_text_translingual', view_func=self.voice_to_text_translingual, methods=['POST'])
        return app

    def index(self):
        return "OK"

    def heartbeat(self):
        return "OK"

    def train(self):
        try:
            settings = json.loads(flask.request.form['settings'])
            voice = settings['voice']
            path = f'/resources/voices/'
            os.makedirs(path, exist_ok=True)
            path +=voice+'.wav'
            flask.request.files['file'].save(path)
            self.model.add_zero_shot_spk(settings['text'], path, voice)
            self.model.save_spkinfo()
            return "OK"
        except:
            return traceback.format_exc(), 500

    def _read_and_return(self, en):
        for content in en:
            buf = io.BytesIO()
            torchaudio.save(buf, content['tts_speech'], self.model.sample_rate, format="wav")
            buf.seek(0)
            return flask.send_file(
                buf,
                mimetype="audio/wav",
            )

    def voice_to_file(self):
        os.makedirs('/resources/temp', exist_ok=True)
        template_name = f'/resources/temp/{uuid.uuid4()}.wav'
        try:
            settings = json.loads(flask.request.form['settings'])
            voice = f'/resources/voices/{settings["voice"]}.wav'
            flask.request.files['file'].save(template_name)
            result = self._read_and_return(self.model.inference_vc(template_name, voice, stream=False))
            return result
        except:
            return traceback.format_exc(), 500
        finally:
            if os.path.isfile(template_name):
                os.unlink(template_name)

    def voice_to_text(self):
        try:
            settings = json.loads(flask.request.form['settings'])
            voice = settings["voice"]
            text = settings["text"]
            return self._read_and_return(self.model.inference_zero_shot(
                text,
                prompt_text='',
                prompt_wav=None,
                zero_shot_spk_id=voice
            ))
        except:
            return traceback.format_exc(), 500

    def voice_to_text_translingual(self):
        try:
            settings = json.loads(flask.request.form['settings'])
            voice = settings["voice"]
            text = settings["text"]
            return self._read_and_return(self.model.inference_cross_lingual(
                text, prompt_wav=None, zero_shot_spk_id=voice, stream=False
            ))
        except:
            return traceback.format_exc(), 500

