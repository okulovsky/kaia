from pathlib import Path
import rhasspynlu
from rhasspyasr_kaldi.transcribe import KaldiCommandLineTranscriber
from utils import kaldi_path
from rhasspynlu.fsticuffs import recognize


class Transcriber:
    def __init__(self,
                 path: Path
                 ):
        with open(path / 'intent_graph.pickle.gz', 'rb') as file:
            self.graph = rhasspynlu.gzip_pickle_to_graph(file)

        self.transcriber = KaldiCommandLineTranscriber(
            model_type = 'nnet3',
            model_dir = path / 'kaldi/model',
            graph_dir = path / 'kaldi/model/graph',
            port_num = 50847,
            kaldi_dir = kaldi_path,
            kaldi_args = None
        )

    def transcribe(self, wav: bytes):
        # Parameters 16000, 2, 1 are actually not correct for test items.
        # It doesn't seem that in Rhasspy these parameters are possible to change for Kaldi transcriber
        # They might not matter. If they do, some workaround needs to be developed to obtain them
        transcription = self.transcriber.transcribe_stream([wav], 16000, 2, 1)

        recognition = recognize(
            tokens = transcription.text,
            graph = self.graph,
            fuzzy = True,
            stop_words = None,
            word_transform=str.lower,
            converters=None,
            extra_converters={},
        )

        from copy import copy
        js_recognition = []
        for rec in recognition:
            js_rec = copy(rec.__dict__)
            js_rec['entities'] = [e.__dict__ for e in js_rec['entities']]
            js_recognition.append(js_rec)

        js_transcription = copy(transcription.__dict__)
        js_transcription['tokens'] = [t.__dict__ for t in js_transcription['tokens']]

        result = dict(fsticuffs=js_recognition, kaldi=js_transcription)
        return result

