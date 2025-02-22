import pickle
import traceback
import flask
import os
from zonos_model import ZonosModel
from pathlib import Path
import subprocess

def concat_with_mpeg(temp_file, output_path, paths):
    control_content_array = [f"file '{p}'" for p in paths]
    control_content = '\n'.join(control_content_array)
    with open(temp_file, 'w') as stream:
        stream.write(control_content)

    args = [
        'ffmpeg',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        str(temp_file),
        '-y',
        str(output_path)
    ]
    try:
        subprocess.check_output(args)
    except subprocess.CalledProcessError as err:
        raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}. Output\n{err.output}')


class ZonosApp:
    def __init__(self, model: ZonosModel):
        self.model = model
        self.loaded_speakers = dict()

    def create_app(self):
        app = flask.Flask(type(self).__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/train/<speaker>', view_func=self.train, methods = ['POST'])
        app.add_url_rule('/voiceover', view_func=self.voiceover, methods=['POST'])
        return app

    def index(self):
        return "OK"

    def train(self, speaker: str):
        tmp_file = Path('temp.wav')
        try:
            source_folder = Path(f'/voices/{speaker}/')
            paths = [source_folder / f for f in os.listdir(source_folder)]
            concat_with_mpeg('files.tmp', tmp_file, paths)

            speaker_model = self.model.train(tmp_file)
            with open(f'/speakers/{speaker}', 'wb') as file:
                pickle.dump(speaker_model, file)
            self.loaded_speakers[speaker] = speaker_model
            return "OK"
        except:
            return traceback.format_exc(), 500
        finally:
            if tmp_file.is_file():
                os.unlink(tmp_file)

    def voiceover(self):
        output_file = Path(__file__).parent/'output.wav'
        try:
            data: dict = flask.request.json
            speaker = data['speaker']
            if speaker not in self.loaded_speakers:
                speaker_path = Path(f'/speakers/{speaker}')
                if not speaker_path.is_file():
                    raise ValueError(f"Speaker {speaker} was not trained")
                with open(speaker_path, 'rb') as stream:
                    self.loaded_speakers[speaker] = pickle.load(stream)
            text = data['text']
            language = data['language']
            self.model.voiceover(text, self.loaded_speakers[speaker], language, output_file)
            return flask.send_file(output_file)
        except:
            return traceback.format_exc(), 500
        finally:
            if output_file.is_file():
                os.unlink(output_file)
