"""
Benchmark: plain Whisper vs Whisper + KenLM LogitsProcessor.
WER comparison by accent.

Usage:
    uv run python research/whisper_kenlm_benchmark.py
    uv run python research/whisper_kenlm_benchmark.py --samples 30 --weight 1.0
    uv run python research/whisper_kenlm_benchmark.py --model openai/whisper-base --beams 5
"""
import sys, argparse, json, zipfile, os
sys.path.insert(0, 'research')

import torch
import numpy as np
from collections import defaultdict
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from jiwer import wer as compute_wer
from audio_utils import decode_for_whisper, WHISPER_SR
from kenlm_processor import KenLMLogitsProcessor

DATASET_ZIP = 'research/voice-dataset.zip'
AUDIO_DIR   = 'research/to_zip'
LM_BINARY   = 'research/lm/lm.binary'


def pick_device() -> str:
    if torch.backends.mps.is_available(): return 'mps'
    if torch.cuda.is_available(): return 'cuda'
    return 'cpu'


def load_samples(n_per_accent: int) -> list[dict]:
    z = zipfile.ZipFile(DATASET_ZIP)
    meta = json.loads(z.read('to_zip/samples.json'))
    by_speaker = defaultdict(list)
    for m in meta:
        if os.path.exists(f"{AUDIO_DIR}/{m['filename']}"):
            by_speaker[m['speaker']].append(m)
    result = []
    for items in by_speaker.values():
        result.extend(items[:n_per_accent])
    return result


def transcribe(audio: np.ndarray, processor, model, device: str,
               logits_processor=None, num_beams: int = 1) -> str:
    inputs = processor(audio, sampling_rate=WHISPER_SR, return_tensors='pt',
                       return_attention_mask=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    kwargs = dict(task='transcribe', num_beams=num_beams)
    if logits_processor:
        kwargs['logits_processor'] = [logits_processor]
    with torch.no_grad():
        out = model.generate(**inputs, **kwargs)
    return processor.batch_decode(out, skip_special_tokens=True)[0].strip().lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--model',   default='openai/whisper-base')
    parser.add_argument('--weight',  type=float, default=0.5)
    parser.add_argument('--beams',   type=int, default=1)
    args = parser.parse_args()

    device = pick_device()
    print(f"model={args.model}  device={device}  beams={args.beams}  λ={args.weight}  n={args.samples}\n")

    processor = WhisperProcessor.from_pretrained(args.model)
    model     = WhisperForConditionalGeneration.from_pretrained(args.model).to(device)
    kenlm_lp  = KenLMLogitsProcessor(LM_BINARY, processor.tokenizer, weight=args.weight)

    samples    = load_samples(args.samples)
    by_speaker = defaultdict(list)
    for s in samples:
        by_speaker[s['speaker']].append(s)

    all_refs, all_plain, all_kenlm = [], [], []

    print(f"{'Accent':<12} {'N':>4}  {'Plain WER':>10}  {'KenLM WER':>10}  {'Δ':>8}")
    print('─' * 52)

    for speaker, items in sorted(by_speaker.items()):
        refs, plain_preds, kenlm_preds = [], [], []
        for i, s in enumerate(items):
            audio = decode_for_whisper(f"{AUDIO_DIR}/{s['filename']}")
            refs.append(s['text'].strip().lower())
            plain_preds.append(transcribe(audio, processor, model, device, num_beams=args.beams))
            kenlm_preds.append(transcribe(audio, processor, model, device, kenlm_lp, args.beams))
            if (i + 1) % 5 == 0:
                print(f"  {speaker}: {i+1}/{len(items)}", flush=True)

        plain_wer = compute_wer(refs, plain_preds)
        kenlm_wer = compute_wer(refs, kenlm_preds)
        delta = kenlm_wer - plain_wer
        sign  = '↓' if delta < 0 else '↑'
        print(f"{speaker:<12} {len(refs):>4}  {plain_wer:>10.1%}  {kenlm_wer:>10.1%}  {sign}{abs(delta):>6.1%}")

        all_refs.extend(refs)
        all_plain.extend(plain_preds)
        all_kenlm.extend(kenlm_preds)

    print('─' * 52)
    print(f"{'OVERALL':<12} {len(all_refs):>4}  {compute_wer(all_refs, all_plain):>10.1%}  "
          f"{compute_wer(all_refs, all_kenlm):>10.1%}")
    print()
    print("↓ = KenLM улучшил WER. Если ↑ — попробуй меньший --weight")


if __name__ == '__main__':
    main()
