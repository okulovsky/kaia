import sys, argparse, json, zipfile, os, time
sys.path.insert(0, 'research')

import kenlm
import torch
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from jiwer import wer as compute_wer
from audio_utils import decode_for_whisper, WHISPER_SR
from kenlm_processor import KenLMLogitsProcessor, VocabConstraintProcessor, rescore_nbest, _sequence_log_probs

DATASET_ZIP = 'research/voice-dataset.zip'
AUDIO_DIR   = 'research/to_zip'
LM_BINARY   = 'research/lm/lm.binary'


def pick_device():
    if torch.backends.mps.is_available(): return 'mps'
    if torch.cuda.is_available(): return 'cuda'
    return 'cpu'


def load_samples(n):
    z    = zipfile.ZipFile(DATASET_ZIP)
    meta = json.loads(z.read('to_zip/samples.json'))
    return [m for m in meta if os.path.exists(f"{AUDIO_DIR}/{m['filename']}")][:n]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--model',   default='openai/whisper-base')
    parser.add_argument('--weight',  type=float, default=0.5)
    parser.add_argument('--beams',   type=int, default=5)
    parser.add_argument('--hyps',    type=int, default=10)
    args = parser.parse_args()

    device    = pick_device()
    processor = WhisperProcessor.from_pretrained(args.model)
    model     = WhisperForConditionalGeneration.from_pretrained(args.model).to(device)
    lm        = kenlm.Model(LM_BINARY)
    lp        = KenLMLogitsProcessor(lm, processor.tokenizer, weight=args.weight)
    vc        = VocabConstraintProcessor(processor.tokenizer, 'research/text-dataset.json')

    print(f"model={args.model}  device={device}  weight={args.weight}  beams={args.beams}  hyps={args.hyps}  samples={args.samples}\n")

    dummy = np.zeros(WHISPER_SR, dtype=np.float32)
    inp   = processor(dummy, sampling_rate=WHISPER_SR, return_tensors='pt', return_attention_mask=True)
    with torch.no_grad():
        model.generate(**{k: v.to(device) for k, v in inp.items()}, task='transcribe')

    samples = load_samples(args.samples)
    refs, greedy_preds, injection_preds, vocab_preds, nbest_preds = [], [], [], [], []

    print("Transcribing...")
    t0 = time.perf_counter()

    for i, s in enumerate(samples):
        audio  = decode_for_whisper(f"{AUDIO_DIR}/{s['filename']}")
        inputs = processor(audio, sampling_rate=WHISPER_SR, return_tensors='pt',
                           return_attention_mask=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            g = model.generate(**inputs, task='transcribe')
        greedy = processor.batch_decode(g, skip_special_tokens=True)[0].strip().lower()

        with torch.no_grad():
            inj = model.generate(
                **inputs, task='transcribe',
                num_beams=args.beams,
                logits_processor=[lp],
                no_repeat_ngram_size=3,
                condition_on_prev_tokens=False,
            )
        injection = processor.batch_decode(inj, skip_special_tokens=True)[0].strip().lower()

        with torch.no_grad():
            vc_out = model.generate(
                **inputs, task='transcribe',
                num_beams=args.beams,
                logits_processor=[vc],
                condition_on_prev_tokens=False,
            )
        vocab_pred = processor.batch_decode(vc_out, skip_special_tokens=True)[0].strip().lower()

        nbest, _ = rescore_nbest(audio, processor, model, device, lm,
                                 weight=args.weight, num_hyps=args.hyps)

        refs.append(s['text'].strip().lower())
        greedy_preds.append(greedy)
        injection_preds.append(injection)
        vocab_preds.append(vocab_pred)
        nbest_preds.append(nbest)

        print(f"  [{i+1}/{len(samples)}] {(time.perf_counter()-t0)/(i+1):.1f}s/sample", flush=True)

    greedy_wer    = compute_wer(refs, greedy_preds)
    injection_wer = compute_wer(refs, injection_preds)
    vocab_wer     = compute_wer(refs, vocab_preds)
    nbest_wer     = compute_wer(refs, nbest_preds)

    def row(label, wer):
        d = wer - greedy_wer
        mark = f"↓ -{abs(d):.1%}" if d < -0.001 else (f"→  0.0%" if abs(d) < 0.001 else f"↑ +{d:.1%}")
        print(f"  {label:<38} {wer:>6.1%}  {mark}")

    print(f"\nResults ({len(samples)} samples):\n")
    print(f"  {'Method':<38} {'WER':>6}  {'vs greedy'}")
    print(f"  {'─'*38} {'─'*6}  {'─'*10}")
    row("Greedy (baseline)", greedy_wer)
    row(f"Vocab constraint (beams={args.beams})", vocab_wer)
    row(f"Logits injection (beams={args.beams}, λ={args.weight})", injection_wer)
    row(f"N-best rescoring (hyps={args.hyps}, λ={args.weight})", nbest_wer)


if __name__ == '__main__':
    main()
