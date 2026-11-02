"""Trains the n-gram LM of Nemotron's greedy decoder from a dataset.json.

The words of the ARPA are the ids of the model's SentencePiece tokens, one line of ids per text. Each line is what
the decoder emits for this text: capitals and punctuation as they are, and the language tag closing the sentence.
Needs sentencepiece, gguf and the whisper_ken_lm image, not BrainBox:

    python train_token_lm.py data/nlu_testbed/dataset.json model.gguf nlu.arpa

The ARPA goes to the models folder of the decider's resources, and a model in installation.yaml names it
with `lm_filename` and `lm_weight`.
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
from gguf import GGUFReader
from sentencepiece import SentencePieceProcessor

TAGS = dict(en='<en-US>', de='<de-DE>', ru='<ru-RU>')
LMPLZ = ['docker', 'run', '--rm', '-i', '--entrypoint', 'lmplz', 'whisper_ken_lm', '-o', '3', '--discount_fallback']


def read_tokenizer(model_path: str) -> SentencePieceProcessor:
    field = GGUFReader(model_path).get_field('asr.tokenizer.spm_model')
    if field is None:
        raise ValueError(f'{model_path} has no tokenizer: take the GGUF of Hugging Face revision ea30d66 or a newer one')
    return SentencePieceProcessor(model_proto=base64.b64decode(field.contents()))


def main(dataset_path: str, model_path: str, arpa_path: str):
    with open(dataset_path, encoding='utf-8') as file:
        samples = json.load(file)
    tokenizer = read_tokenizer(model_path)
    # A failed run must not leave a cut ARPA in place of a good one
    partial = arpa_path + '.partial'
    with tempfile.TemporaryFile('w+') as corpus, open(partial, 'w') as arpa:
        for sample in samples:
            tokens = tokenizer.encode(f"{sample['text']} {TAGS[sample['language']]}")
            corpus.write(' '.join(map(str, tokens)) + '\n')
        corpus.seek(0)
        subprocess.run(LMPLZ, stdin=corpus, stdout=arpa, check=True)
    os.replace(partial, arpa_path)


if __name__ == '__main__':
    main(*sys.argv[1:])
