"""
Real-time Whisper streaming demo.

Usage:
    uv run python research/whisper_realtime.py audio.wav
    uv run python research/whisper_realtime.py audio.wav --chunks 5
    uv run python research/whisper_realtime.py audio.wav --model openai/whisper-tiny
"""
import sys, argparse, time
sys.path.insert(0, 'research')

import numpy as np
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from audio_utils import decode_for_whisper, WHISPER_SR


def pick_device() -> str:
    if torch.backends.mps.is_available(): return 'mps'
    if torch.cuda.is_available(): return 'cuda'
    return 'cpu'


def transcribe(audio: np.ndarray, processor, model, device: str) -> str:
    inputs = processor(audio, sampling_rate=WHISPER_SR, return_tensors='pt',
                       return_attention_mask=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(**inputs, task='transcribe')
    return processor.batch_decode(out, skip_special_tokens=True)[0].strip()


def common_prefix(a: list[str], b: list[str]) -> list[str]:
    result = []
    for x, y in zip(a, b):
        if x == y: result.append(x)
        else: break
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='audio file (wav, mp3, aac, ...)')
    parser.add_argument('--chunks', type=int, default=10, help='split audio into N equal chunks')
    parser.add_argument('--model',  default='openai/whisper-base')
    args = parser.parse_args()

    device = pick_device()
    print(f"model={args.model}  device={device}  chunks={args.chunks}\n")

    processor = WhisperProcessor.from_pretrained(args.model)
    model = WhisperForConditionalGeneration.from_pretrained(args.model).to(device)

    dummy = np.zeros(WHISPER_SR, dtype=np.float32)
    transcribe(dummy, processor, model, device)  # warmup

    audio = decode_for_whisper(args.file)
    dur   = len(audio) / WHISPER_SR
    step  = len(audio) // args.chunks
    print(f"duration: {dur:.2f}s  chunk size: {step/WHISPER_SR:.2f}s\n")

    committed: list[str] = []
    prev:      list[str] = []
    latencies = []

    print(f"{'t':>6}  {'lat':>7}  {'RTF':>6}  committed / pending")
    print('─' * 72)

    for end in range(step, len(audio) + step, step):
        buffer   = audio[:min(end, len(audio))]
        t_audio  = len(buffer) / WHISPER_SR

        t0   = time.perf_counter()
        text = transcribe(buffer, processor, model, device)
        lat  = time.perf_counter() - t0
        latencies.append(lat)

        curr = text.split()
        stable = common_prefix(prev, curr)
        newly  = stable[len(committed):]
        committed.extend(newly)

        pending = curr[len(committed):]
        display = ' '.join(committed)
        if pending:
            display += '  /  ' + ' '.join(pending)

        print(f"{t_audio:5.1f}s  {lat*1000:5.0f}ms  {lat/t_audio:5.2f}x  {display}")
        prev = curr

    print('─' * 72)
    lats = np.array(latencies)
    ends = np.array([min((i+1)*step/WHISPER_SR, dur) for i in range(len(lats))])

    print(f"avg latency: {lats.mean()*1000:.0f}ms   avg RTF: {(lats/ends).mean():.3f}x")
    print(f"final: {text!r}")


if __name__ == '__main__':
    main()
