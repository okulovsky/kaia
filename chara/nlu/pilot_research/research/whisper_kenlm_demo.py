import sys, argparse, json, zipfile, os
sys.path.insert(0, 'research')

import kenlm
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from audio_utils import decode_for_whisper, WHISPER_SR

DATASET_ZIP = 'research/voice-dataset.zip'
AUDIO_DIR   = 'research/to_zip'
LM_BINARY   = 'research/lm/lm.binary'


def pick_device():
    if torch.backends.mps.is_available(): return 'mps'
    if torch.cuda.is_available(): return 'cuda'
    return 'cpu'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=4)
    args = parser.parse_args()

    device    = pick_device()
    processor = WhisperProcessor.from_pretrained('openai/whisper-base')
    model     = WhisperForConditionalGeneration.from_pretrained('openai/whisper-base').to(device)
    lm        = kenlm.Model(LM_BINARY)

    meta    = json.loads(zipfile.ZipFile(DATASET_ZIP).read('to_zip/samples.json'))
    samples = [m for m in meta if os.path.exists(f"{AUDIO_DIR}/{m['filename']}")][:args.samples]

    for s in samples:
        audio  = decode_for_whisper(f"{AUDIO_DIR}/{s['filename']}")
        inputs = processor(audio, sampling_rate=WHISPER_SR, return_tensors='pt',
                           return_attention_mask=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            out = model.generate(
                **inputs, task='transcribe',
                do_sample=True, temperature=0.2, top_k=50,
                num_return_sequences=5,
                no_repeat_ngram_size=3,
                condition_on_prev_tokens=False,
                output_scores=True, return_dict_in_generate=True,
            )
        texts    = [processor.decode(seq, skip_special_tokens=True).strip() for seq in out.sequences]
        lm_scores = [lm.score(t.lower(), bos=True, eos=True) for t in texts]
        best_j   = max(range(5), key=lambda i: lm_scores[i])

        print(f"ref      : {s['text']}")
        for i, (t, sc) in enumerate(zip(texts, lm_scores)):
            marker = ' - kenlm' if i == best_j else ''
            print(f"hyp {i+1}    : {t}  (lm={sc:.1f}){marker}")
        print()


if __name__ == '__main__':
    main()
