import pickle
import sys
import flask
from pathlib import Path
import os
import traceback
from generate import Generator
from tortoise.api import TextToSpeech
import sys
import argparse
import subprocess
from io import BytesIO

DEFAULT_MODELS_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'models')
MODELS_DIR = os.environ.get('TORTOISE_MODELS_DIR', DEFAULT_MODELS_DIR)


generator = None
app = flask.Flask("TortoiseTTSApp")


@app.route('/', methods=['GET'])
def index():
    return 'OK'



@app.route('/dub', methods=['POST'])
def dub():
    try:
        data = flask.request.json
        voice = data['voice']
        text = data['text']
        count = int(data['count'])
        result = generator.simple(text, voice, count)
        js = flask.jsonify(result)
        return js
    except:
        return traceback.format_exc(), 500




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--install', action='store_true')
    parser.add_argument('-n','--notebook', action='store_true')
    args = parser.parse_args()

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0', "--NotebookApp.token=''"], cwd='/repo')
        exit(0)


    tts = TextToSpeech()
    if args.install:
        exit(0)

    generator = Generator(tts)
    app.run(port = 8084, host='0.0.0.0')





