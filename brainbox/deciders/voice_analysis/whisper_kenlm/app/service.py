import os, shutil, subprocess, uuid
from pathlib import Path

import numpy as np
import soundfile as sf

from foundation_kaia.marshalling import FileLike, FileLikeHandler
from interface import IWhisperKenLM
from model import WhisperKenLMState


class WhisperKenLMService(IWhisperKenLM):
    def __init__(self, storage):
        self.storage = storage

    def _state(self) -> WhisperKenLMState:
        return self.storage.get_model_data(None).model

    def train_lm(self, corpus: str) -> None:
        lm_dir = Path('/resources/lm')
        lm_dir.mkdir(exist_ok=True)
        corpus_path = lm_dir / 'corpus.txt'
        arpa_path   = lm_dir / 'lm.arpa'
        binary_path = lm_dir / 'lm.binary'
        corpus_path.write_text(corpus)
        lmplz_bin = _find_bin('lmplz')
        build_bin  = _find_bin('build_binary')
        with corpus_path.open() as inp, arpa_path.open('w') as out:
            subprocess.run([lmplz_bin, '-o', '3', '--discount_fallback'], stdin=inp, stdout=out, check=True)
        subprocess.run([build_bin, str(arpa_path), str(binary_path)], check=True)
        import kenlm
        new_lm = kenlm.Model(str(binary_path))
        if self.storage.model is not None:
            self.storage.model.model.lm = new_lm

    def transcribe(self, file: FileLike, weight: float = 0.5, beams: int = 5) -> str:
        import torch
        from kenlm_processor import KenLMLogitsProcessor
        state  = self._state()
        audio  = _decode_audio(file)
        inputs = state.processor(audio, sampling_rate=16000, return_tensors='pt', return_attention_mask=True)
        kwargs = {
            'task': 'transcribe',
            'num_beams': beams,
            'no_repeat_ngram_size': 3,
            'condition_on_prev_tokens': False,
        }
        if state.lm is not None:
            kwargs['logits_processor'] = [KenLMLogitsProcessor(state.lm, state.processor.tokenizer, weight=weight)]
        with torch.no_grad():
            out = state.model.generate(**inputs, **kwargs)
        return state.processor.batch_decode(out, skip_special_tokens=True)[0].strip()


def _find_bin(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    local = Path.home() / '.local/bin' / name
    if local.exists():
        return str(local)
    raise FileNotFoundError(f'{name} not found')


def _decode_audio(file: FileLike) -> np.ndarray:
    uid = str(uuid.uuid4())
    inp = f'/tmp/{uid}'
    out = f'/tmp/{uid}.wav'
    try:
        FileLikeHandler.write(file, inp)
        subprocess.run(
            ['ffmpeg', '-y', '-i', inp, '-ar', '16000', '-ac', '1', '-f', 'wav', out],
            check=True, capture_output=True,
        )
        audio, _ = sf.read(out, dtype='float32')
        return audio
    finally:
        for p in (inp, out):
            if os.path.exists(p):
                os.unlink(p)
