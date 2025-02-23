import shutil
import traceback
import flask
import os
from model import Model
from pathlib import Path
import pickle
import uuid

class ZonosApp:
    def __init__(self, model: Model):
        self.model = model
        self.voices_folder = Path('/voices')
        self.speakers_folder = Path('/speakers')
        self.speakers_cache = {}

    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/train/<speaker>', view_func=self.train, methods=['POST'])
        app.add_url_rule('/voiceover', view_func=self.voiceover, methods=['POST'])
        return app

    def index(self):
        return "OK"

    def train(self, speaker):
        try:
            voice_folder = self.voices_folder/speaker
            shutil.rmtree(voice_folder, ignore_errors=True)
            os.makedirs(voice_folder)
            for filename, content in flask.request.files.items():
                content.save(voice_folder/filename)
                embedding = self.model.compute_embedding(voice_folder/filename)
                self.speakers_cache[speaker] = embedding
                with open(self.speakers_folder/speaker, 'wb') as stream:
                    pickle.dump(embedding, stream)
            return "OK"
        except:
            return traceback.format_exc(), 500

    def voiceover(self):
        temp_file = Path(__file__).parent/f'{uuid.uuid4()}.wav'
        try:
            speaker = flask.request.json['speaker']
            if speaker not in self.speakers_cache:
                speaker_file = self.speakers_folder/speaker
                if not speaker_file.is_file():
                    raise ValueError(f"Speaker {speaker} was not trained")
                with open(speaker_file, 'rb') as stream:
                    self.speakers_cache[speaker] = pickle.load(stream)
            self.model.voiceover(
                flask.request.json['text'],
                speaker,
                flask.request.json['language'],
                temp_file
            )
            return flask.send_file(temp_file)
        except:
            return traceback.format_exc(), 500
        finally:
            if temp_file.is_file():
                os.unlink(temp_file)


