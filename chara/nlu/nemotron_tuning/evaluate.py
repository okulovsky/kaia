"""
The WER per language of Nemotron on a manifest: the base model, or a model merged by train_lora.py.

    python chara/nlu/nemotron_tuning/evaluate.py --manifest <data>/real.jsonl
    python chara/nlu/nemotron_tuning/evaluate.py --manifest <data>/real.jsonl --model <run>/merged --out <run>/real.json

The decoding is offline (the whole recording at once); the runtime streams, so check the GGUF in Kaia as well.
"""
import argparse
import json
from pathlib import Path
import torch
from transformers import AutoProcessor, Nemotron3_5AsrForRNNT
import manifest
from train_lora import MODEL, REVISION, transcribe, word_error_rate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--model', default=None, help='a merged model folder; the base model if not given')
    parser.add_argument('--out', default=None)
    parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = parser.parse_args()

    source = dict(pretrained_model_name_or_path=args.model) if args.model else dict(pretrained_model_name_or_path=MODEL, revision=REVISION)
    processor = AutoProcessor.from_pretrained(**source)
    model = Nemotron3_5AsrForRNNT.from_pretrained(**source, torch_dtype=torch.float32).to(args.device)
    items = manifest.read(args.manifest)
    texts = transcribe(model, processor, items, args.device)
    wer = word_error_rate(items, texts)
    exact = sum(manifest.normalize(i['text']) == manifest.normalize(t) for i, t in zip(items, texts))
    print(f'WER {wer}, exact {exact}/{len(items)}')
    for item, text in zip(items, texts):
        if manifest.normalize(item['text']) != manifest.normalize(text):
            print(f'   {item["text"]!r} -> {text!r}')
    if args.out:
        Path(args.out).write_text(json.dumps(dict(
            model=args.model or MODEL, wer=wer, exact=exact, count=len(items),
            results=[dict(audio=i['audio'], expected=i['text'], text=t) for i, t in zip(items, texts)],
        ), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
