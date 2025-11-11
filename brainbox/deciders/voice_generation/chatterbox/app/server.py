import traceback
import flask
import os
import pickle
import shutil
import uuid
from model import Model
from pathlib import Path
from chatterbox.mtl_tts import Conditionals 

class ChatterboxApp:
    def __init__(self, model: Model):
        self.model = model
        self.voices_folder = Path('/voices')
        self.speakers_folder = Path('/speakers')
        self.speakers_cache = {}

    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/heartbeat', view_func=self.heartbeat, methods=['GET'])
        app.add_url_rule('/train/<speaker>', view_func=self.train, methods = ['POST'])
        app.add_url_rule('/voiceover', view_func=self.voiceover, methods = ['POST'])
        return app

    def index(self):
        return "OK"

    def heartbeat(self):
        return "OK" 

    def train(self, speaker):
        try:
            voice_folder = self.voices_folder / speaker
            shutil.rmtree(voice_folder, ignore_errors=True)
            os.makedirs(voice_folder)
            for filename, content in flask.request.files.items():
                file_path = voice_folder / filename
                content.save(file_path)
                embedding = self.model.compute_embedding(file_path) 
                self.speakers_cache[speaker] = embedding
                embedding.save(self.speakers_folder / speaker)  
            return "OK"
        except:
            return traceback.format_exc(), 500

    def voiceover(self):
        try:
            test_file = Path(__file__).parent / 'test_write.txt'
            with open(test_file, 'w') as f:
                f.write('test')
            os.unlink(test_file)
            print("Test write succeeded in current dir")
        except Exception as e:
            print(f"Test write failed: {e}")
        # temp_file = Path(__file__).parent / f'{uuid.uuid4()}.wav'
        temp_file = Path('/file_cache') / f'{uuid.uuid4()}.wav'
        try:
            speaker = flask.request.json['speaker']
            if speaker not in self.speakers_cache:
                speaker_file = self.speakers_folder / speaker
                if not speaker_file.is_file():
                    raise ValueError(f"Speaker {speaker} was not trained")
                self.speakers_cache[speaker] = Conditionals.load(speaker_file)  # Загружаем через load
            self.model.voiceover(
                flask.request.json['text'],
                self.speakers_cache[speaker],  
                flask.request.json['language'],
                temp_file
            )
            return flask.send_file(temp_file)
        except:
            return traceback.format_exc(), 500
        finally:
            if temp_file.is_file():
                os.unlink(temp_file)
        

    def decide(self):
        try:
            data = flask.request.json
            return flask.jsonify(dict(
                arguments=data,
                success = True
            ))
        except:
            return traceback.format_exc(), 500

