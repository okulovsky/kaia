import sys
import flask
from pathlib import Path
import os
import traceback
from generate import Generator
from tortoise.api import TextToSpeech
import sys

DEFAULT_MODELS_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'models')
MODELS_DIR = os.environ.get('TORTOISE_MODELS_DIR', DEFAULT_MODELS_DIR)


generator = None
app = flask.Flask("TortoiseTTSApp")


@app.route('/', methods=['GET'])
def index():
    return 'OK'

def _run(method):
    try:
        data = flask.request.json
        voice = data['voice']
        text = data['text']
        count = int(data['count'])
        result = method(text, voice, count)
        js = flask.jsonify(result)
        return js
    except:
        return 500, traceback.format_exc()


@app.route('/dub', methods=['POST'])
def dub():
    return _run(generator.simple)


@app.route('/aligned_dub', methods=['POST'])
def aligned_dub():
    return _run(generator.alignment)


if __name__ == '__main__':
    tts = TextToSpeech()
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        exit(0)
    generator = Generator(tts)
    app.run(port = 8084, host='0.0.0.0')





