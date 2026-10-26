"""
LoRA fine-tuning of Nemotron 3.5 ASR with Transformers, in its own environment (requirements.txt), on a GPU or a CPU.

    python chara/nlu/nemotron_tuning/train_lora.py --train <data>/train.jsonl --dev <data>/dev.jsonl --out <run>

The best adapter by the WER on the dev set is kept in <run>/adapter, and merged into the weights in <run>/merged,
which export_gguf.py converts for NeMo-Speech.cpp. See README.md for the settings.
"""
import argparse
import json
import random
import time
from pathlib import Path
import librosa
import numpy as np
import soundfile
import torch
import torchaudio
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoProcessor, Nemotron3_5AsrForRNNT, get_cosine_schedule_with_warmup
import manifest

MODEL = 'nvidia/nemotron-3.5-asr-streaming-0.6b'
REVISION = 'ea30d66debe3740a08b573244286791d423d6b3e'
SAMPLE_RATE = 16000
LAYER = r'encoder\.layers\.\d+\.'
TARGETS = {
    'attention': LAYER + r'self_attn\.(q_proj|k_proj|v_proj|o_proj)',
    'encoder': LAYER + r'(self_attn\.(q_proj|k_proj|v_proj|o_proj)|feed_forward[12]\.linear[12])',
    'all': r'(' + LAYER + r'(self_attn\.(q_proj|k_proj|v_proj|o_proj)|feed_forward[12]\.linear[12])'
           r'|encoder_projector|decoder\.decoder_projector|joint\.head|prompt_projector\.linear_[12])',
}


def load_audio(path: str) -> np.ndarray:
    audio, rate = soundfile.read(path, dtype='float32', always_2d=True)
    audio = audio.mean(axis=1)
    if rate != SAMPLE_RATE:
        audio = librosa.resample(audio, orig_sr=rate, target_sr=SAMPLE_RATE)
    return audio


class Augmentation:
    """Speed, gain and noise, drawn anew for every use of a recording"""
    def __init__(self, noise_files: list[str], probability: float, snr: tuple[float, float], rnd: random.Random):
        self.noises = [load_audio(f) for f in noise_files]
        self.probability = probability
        self.snr = snr
        self.rnd = rnd

    def __call__(self, audio: np.ndarray) -> np.ndarray:
        if self.rnd.random() < self.probability:
            speed = self.rnd.uniform(0.9, 1.1)
            audio = librosa.resample(audio, orig_sr=int(SAMPLE_RATE * speed), target_sr=SAMPLE_RATE)
        if self.rnd.random() < self.probability:
            audio = audio * 10 ** (self.rnd.uniform(-10, 6) / 20)
        if self.rnd.random() < self.probability:
            noise = self._noise(len(audio))
            power = np.mean(audio ** 2) + 1e-10
            snr = self.rnd.uniform(*self.snr)
            audio = audio + noise * np.sqrt(power / (np.mean(noise ** 2) + 1e-10) / 10 ** (snr / 10))
        return np.clip(audio, -1, 1).astype(np.float32)

    def _noise(self, length: int) -> np.ndarray:
        if self.noises:
            noise = self.rnd.choice(self.noises)
            if len(noise) < length:
                noise = np.tile(noise, length // len(noise) + 1)
            start = self.rnd.randrange(len(noise) - length + 1)
            return noise[start:start + length]
        # Without recorded noise: white noise coloured towards the low frequencies, as in a room
        white = np.random.default_rng(self.rnd.randrange(1 << 30)).standard_normal(length).astype(np.float32)
        return np.convolve(white, np.ones(8) / 8, mode='same')


def make_batch(processor, model, items: list[dict], augmentation: Augmentation | None, device):
    audios = [load_audio(i['audio']) for i in items]
    if augmentation is not None:
        audios = [augmentation(a) for a in audios]
    inputs = processor(audios, text=[i['text'] for i in items], sampling_rate=SAMPLE_RATE,
                       language=[i['language'] for i in items], return_tensors='pt', padding=True)
    # The processor starts the decoder with its `<blank>`, which is outside of the model's vocabulary;
    # the model's blank is config.blank_token_id, the same id the labels are padded with
    decoder_ids = inputs['decoder_input_ids']
    decoder_ids[decoder_ids >= model.config.vocab_size] = model.config.blank_token_id
    return {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}


def rnnt_loss(base, logits, labels, attention_mask, max_per_token: float):
    """
    The RNN-T loss per label token of each utterance (Transformers 5.20 does not wire it for this model).
    An utterance whose transcript does not fit its audio gives a huge loss that would steer the whole step: it is skipped.
    """
    blank = base.config.blank_token_id
    logit_lengths = base._get_subsampling_output_length(attention_mask.sum(-1)).clamp(max=logits.shape[1])
    label_lengths = (labels != blank).sum(-1)
    frames, tokens = int(logit_lengths.max()), int(label_lengths.max())
    losses = torchaudio.functional.rnnt_loss(
        logits[:, :frames, :tokens + 1].float().contiguous(), labels[:, :tokens].int().contiguous(),
        logit_lengths.int(), label_lengths.int(), blank=blank, reduction='none')
    per_token = losses / label_lengths.clamp(min=1)
    keep = per_token < max_per_token
    if not bool(keep.any()):
        return None, len(keep)
    return per_token[keep].mean(), int((~keep).sum())


def transcribe(model, processor, items: list[dict], device) -> list[str]:
    texts = []
    model.eval()
    with torch.no_grad():
        for item in items:
            inputs = processor(load_audio(item['audio']), sampling_rate=SAMPLE_RATE, language=item['language'], return_tensors='pt')
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
            output = model.generate(**inputs)
            ids = output.sequences if hasattr(output, 'sequences') else output
            texts.append(processor.batch_decode(ids, skip_special_tokens=True)[0].strip())
    model.train()
    return texts


def word_error_rate(items: list[dict], texts: list[str]) -> dict:
    """WER in total and per language"""
    result = {}
    for language in sorted({i['language'] for i in items}) + ['all']:
        pairs = [(i, t) for i, t in zip(items, texts) if language in ('all', i['language'])]
        errors = [manifest.word_errors(i['text'], t) for i, t in pairs]
        result[language] = round(sum(e for e, _ in errors) / max(1, sum(n for _, n in errors)), 4)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='append', required=True, help='manifest, can be repeated')
    parser.add_argument('--dev', required=True, help='manifest the best adapter is chosen on')
    parser.add_argument('--replay', action='append', default=[], help='manifest of general speech against forgetting')
    parser.add_argument('--replay-share', type=float, default=0.3, help='the share of the batch taken from --replay')
    parser.add_argument('--out', required=True)
    parser.add_argument('--steps', type=int, default=3000)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--warmup', type=int, default=200)
    parser.add_argument('--rank', type=int, default=16)
    parser.add_argument('--targets', choices=TARGETS, default='encoder')
    parser.add_argument('--max-loss-per-token', type=float, default=20.0)
    parser.add_argument('--augment', type=float, default=0.5, help='the probability of each augmentation')
    parser.add_argument('--noise-dir', default=None, help='folder with noise recordings, e.g. MUSAN noise')
    parser.add_argument('--snr', type=float, nargs=2, default=(5, 30))
    parser.add_argument('--eval-every', type=int, default=250)
    parser.add_argument('--dev-limit', type=int, default=300)
    parser.add_argument('--always-merge', action='store_true', help='merge the last adapter if none got better than the base model')
    parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    rnd = random.Random(args.seed)
    torch.manual_seed(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    train = [r for path in args.train for r in manifest.read(path)]
    replay = [r for path in args.replay for r in manifest.read(path)]
    dev = manifest.read(args.dev)
    dev = rnd.sample(dev, min(args.dev_limit, len(dev)))
    noise_files = sorted(str(p) for p in Path(args.noise_dir).rglob('*.wav')) if args.noise_dir else []
    augmentation = Augmentation(noise_files, args.augment, tuple(args.snr), rnd)
    print(f'train {len(train)}, replay {len(replay)}, dev {len(dev)}, noise files {len(noise_files)}, device {args.device}')

    processor = AutoProcessor.from_pretrained(MODEL, revision=REVISION)
    base = Nemotron3_5AsrForRNNT.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32).to(args.device)
    log = dict(args=vars(args), base_dev=word_error_rate(dev, transcribe(base, processor, dev, args.device)), steps=[])
    print('dev WER before:', log['base_dev'])

    model = get_peft_model(base, LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, target_modules=TARGETS[args.targets]))
    model.print_trainable_parameters()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.01)
    schedule = get_cosine_schedule_with_warmup(optimizer, args.warmup, args.steps)
    autocast = torch.autocast('cuda', dtype=torch.bfloat16) if args.device.startswith('cuda') else torch.autocast('cpu', enabled=False)
    best = log['base_dev']['all']
    model.train()
    for step in range(1, args.steps + 1):
        replay_count = int(round(args.batch * args.replay_share)) if replay else 0
        items = rnd.sample(train, min(args.batch - replay_count, len(train))) + rnd.sample(replay, min(replay_count, len(replay)))
        inputs = make_batch(processor, base, items, augmentation, args.device)
        labels = inputs.pop('labels')
        begin = time.time()
        with autocast:
            logits = model(**inputs).logits
        loss, skipped = rnnt_loss(base, logits, labels, inputs['attention_mask'], args.max_loss_per_token)
        if loss is not None:
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            optimizer.step()
        optimizer.zero_grad()
        schedule.step()
        entry = dict(step=step, loss=None if loss is None else round(loss.item(), 4), skipped=skipped, seconds=round(time.time() - begin, 2))
        if step % args.eval_every == 0 or step == args.steps:
            entry['dev'] = word_error_rate(dev, transcribe(model, processor, dev, args.device))
            if entry['dev']['all'] < best:
                best = entry['dev']['all']
                model.save_pretrained(out/'adapter')
                entry['saved'] = True
        log['steps'].append(entry)
        print(json.dumps(entry), flush=True)
        (out/'log.json').write_text(json.dumps(log, indent=1))

    if not (out/'adapter').exists():
        if not args.always_merge:
            print('The dev WER never got better than the base model; nothing to merge')
            return
        model.save_pretrained(out/'adapter')
    # The best adapter, merged into the weights: the same architecture and names as the base model
    merged = PeftModel.from_pretrained(
        Nemotron3_5AsrForRNNT.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32), out/'adapter'
    ).merge_and_unload()
    merged.save_pretrained(out/'merged')
    processor.save_pretrained(out/'merged')
    print(f'dev WER {log["base_dev"]["all"]} -> {best}; merged model in {out/"merged"}')


if __name__ == '__main__':
    main()
