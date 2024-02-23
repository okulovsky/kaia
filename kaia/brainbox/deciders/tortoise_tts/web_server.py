import sys
from typing import *
import flask
from dataclasses import dataclass
from uuid import uuid4
from pathlib import Path
import shutil
import os
import traceback
import io


@dataclass
class SettingsClass:
    output_folder: Path
    tortoise_tts_path: Path
    load_voices: Callable[[str], Tuple[Any, Any]] = None
    do_tts: Callable[[str, str], Any] = None
    do_tts_alignment: Callable[[str, str], Any] = None

@dataclass
class SettingsHolder:
    current: Optional[SettingsClass] = None

settings = SettingsHolder()


def debug_tts(text, voice, count):
    path = settings.current.tortoise_tts_path/'tortoise/voices'/voice
    file = list(path.glob('*.wav'))[0]
    fname = str(uuid4())+".wav"
    os.makedirs(settings.current.output_folder, exist_ok=True)
    shutil.copy(file, settings.current.output_folder/fname)
    return [dict(text=text, voice=voice, dubs=[fname])]




class RealTTS:
    def __init__(self, tts):
        self.tts = tts

    def _generate(self, text, voice, count):
        from utils.audio import load_voices
        voice_sel = [voice]
        voice_samples, conditioning_latents = load_voices(voice_sel)

        gen, dbg_state = self.tts.tts_with_preset(
            text,
            k=count,
            voice_samples=voice_samples,
            conditioning_latents=conditioning_latents,
            preset='fast',
            use_deterministic_seed=None,
            return_deterministic_state=True,
            cvvp_amount=0
        )

        if not isinstance(gen, list):
            gen = [gen]
        return gen

    def simple(self, text, voice, count):
        from torchaudio import save
        gen = self._generate(text, voice, count)
        fnames = []
        for g in gen:
            fname = str(uuid4()) + ".wav"
            save(settings.current.output_folder / fname, g.squeeze(0).cpu(), 24000)
            fnames.append(fname)
        return fnames

    def alignment(self, text, voice, count):
        from utils.wav2vec_alignment import Wav2VecAlignment
        import torch

        alignment = Wav2VecAlignment()
        gen = self._generate(text, voice, count)
        fnames = []
        for g in gen:
            fname = str(uuid4()) + ".wav.bin"
            alignments = alignment.align(g.squeeze(1), text, 24000)
            data = dict(audio = g, alignment = alignments)
            torch.save(data, settings.current.output_folder/fname)
            fnames.append(fname)

        return fnames


app = flask.Flask("tortoise-tts-gui-server")

@app.route('/exit', methods=['POST'])
def exit():
    if settings.current is not None:
        del settings.current
        settings.current = None
    os._exit(0)

def _run(method):
    try:
        data = flask.request.json
        voice = data['voice']
        text = data['text']
        count = int(data['count'])
        result = method(text, voice, count)
        js = flask.jsonify(result)
    except:
        return flask.jsonify(dict(_exception=traceback.format_exc()))
    return js

@app.route('/dub', methods=['POST'])
def dub():
    return _run(settings.current.do_tts)


@app.route('/aligned_dub', methods=['POST'])
def aligned_dub():
    return _run(settings.current.do_tts_alignment)

@app.route("/status", methods=['GET'])
def status():
    return "ok"


if __name__ == '__main__':
    port = int(sys.argv[1])
    debug = sys.argv[2] == 'debug'
    output_folder = Path(sys.argv[3])
    tortoise_folder = Path(sys.argv[4])

    settings.current = SettingsClass(output_folder, tortoise_folder)

    if debug:
        settings.current.do_tts = debug_tts
    else:
        from api import TextToSpeech, MODELS_DIR
        models_dir = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'models')
        tts = TextToSpeech(models_dir=models_dir)
        real_tts = RealTTS(tts)
        settings.current.do_tts = real_tts.simple
        settings.current.do_tts_alignment = real_tts.alignment

    app.run(port = port)





