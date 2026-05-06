"""
HuggingFace Whisper — streaming prototype with word-level timestamps.

Two approaches:
  1. pipeline with chunk_length_s — handles overlap/stitching, returns word timestamps
  2. model.generate chunk-by-chunk — token timestamps, foundation for KenLM injection

Usage:
    uv run python research/whisper_streaming.py
    uv run python research/whisper_streaming.py --model openai/whisper-base
    uv run python research/whisper_streaming.py --accent sw-1
"""
import sys, argparse, json, zipfile, os
sys.path.insert(0, 'research')

import numpy as np
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline

from audio_utils import decode_for_whisper, WHISPER_SR

DATASET_ZIP = 'research/voice-dataset.zip'
AUDIO_DIR = 'research/to_zip'
DEFAULT_MODEL = 'openai/whisper-tiny'


def pick_device() -> str:
    if torch.backends.mps.is_available():
        return 'mps'
    if torch.cuda.is_available():
        return 'cuda'
    return 'cpu'


def load_sample(accent: str | None) -> dict:
    z = zipfile.ZipFile(DATASET_ZIP)
    samples = json.loads(z.read('to_zip/samples.json'))
    candidates = [s for s in samples if os.path.exists(f"{AUDIO_DIR}/{s['filename']}")]
    if accent:
        candidates = [s for s in candidates if s['speaker'].startswith(accent)]
    if not candidates:
        raise ValueError(f"No samples found for accent={accent!r}")
    candidates.sort(key=lambda s: len(s['text'].split()), reverse=True)
    return candidates[min(5, len(candidates) - 1)]


def section(title: str):
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def demo_pipeline(audio: np.ndarray, model_name: str, device: str) -> str:
    section("Method 1: pipeline — chunked streaming + word timestamps")
    print("chunk_length_s=10, stride=2s overlap\n")

    pipe = pipeline(
        'automatic-speech-recognition',
        model=model_name,
        chunk_length_s=10,
        stride_length_s=(2, 2),
        return_timestamps='word',
        device=device,
    )
    result = pipe({'array': audio, 'sampling_rate': WHISPER_SR})

    print(f"Full text: {result['text'].strip()!r}\n")
    print("Word timestamps:")
    for chunk in (result.get('chunks') or []):
        t0, t1 = chunk['timestamp']
        t1_str = f"{t1:.2f}s" if t1 is not None else "   ?"
        print(f"  [{t0:5.2f}s → {t1_str:7}]  {chunk['text'].strip()!r}")

    return result['text'].strip()


def demo_manual_chunks(audio: np.ndarray, model_name: str, device: str, chunk_sec: int = 8) -> str:
    section("Method 2: manual chunk-by-chunk — token timestamps (KenLM hook point)")
    print(f"chunk={chunk_sec}s, no overlap\n")

    processor = WhisperProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)

    chunk_size = chunk_sec * WHISPER_SR
    chunks = [audio[i:i + chunk_size] for i in range(0, len(audio), chunk_size)]
    chunks = [c for c in chunks if len(c) > WHISPER_SR // 4]
    print(f"Split into {len(chunks)} chunk(s)\n")

    all_text = []
    for i, chunk in enumerate(chunks):
        t_start = i * chunk_sec
        inputs = processor(chunk, sampling_rate=WHISPER_SR, return_tensors='pt', return_attention_mask=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            out = model.generate(
                **inputs,
                return_timestamps=True,
                return_token_timestamps=True,
                return_dict_in_generate=True,
                task='transcribe',
            )

        text = processor.batch_decode(out['sequences'], skip_special_tokens=True)[0].strip()
        token_ts = [round(ts, 2) for ts in out['token_timestamps'][0].tolist()]
        all_text.append(text)

        print(f"  Chunk {i}  [{t_start}s → {t_start + len(chunk) / WHISPER_SR:.1f}s]")
        print(f"    Text:              {text!r}")
        print(f"    Token timestamps:  {token_ts[:8]}{'...' if len(token_ts) > 8 else ''}")

    print("\n  token_timestamps → injection point for KenLM LogitsProcessor")
    return ' '.join(all_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--accent', default=None, help='pl-1, pl-2, sw-1, hu-1, ch-1')
    args = parser.parse_args()

    device = pick_device()
    print(f"Device: {device}  |  Model: {args.model}")

    sample = load_sample(args.accent)
    print(f"\nSample:")
    print(f"  Speaker (accent): {sample['speaker']} / language: {sample['language']}")
    print(f"  Expected text:    {sample['text']!r}")

    audio = decode_for_whisper(f"{AUDIO_DIR}/{sample['filename']}")
    print(f"  Duration:         {len(audio) / WHISPER_SR:.2f}s")

    text1 = demo_pipeline(audio, args.model, device)
    text2 = demo_manual_chunks(audio, args.model, device)

    section("Summary")
    print(f"  Expected : {sample['text']!r}")
    print(f"  Pipeline : {text1!r}")
    print(f"  Manual   : {text2!r}")
    print(f"\n  Accent: {sample['language'].upper()} — errors above are exactly what KenLM targets.")


if __name__ == '__main__':
    main()
