import kenlm
import torch
import torch.nn.functional as F
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration, LogitsProcessor
from audio_utils import decode_for_whisper, WHISPER_SR

TIMESTAMP_BEGIN = 50364


class KenLMLogitsProcessor(LogitsProcessor):
    def __init__(self, lm: kenlm.Model, tokenizer, weight: float = 0.5, top_k: int = 50):
        self.lm      = lm
        self.tok     = tokenizer
        self.weight  = weight
        self.top_k   = top_k
        self._word_ids = {
            tid for tid in range(TIMESTAMP_BEGIN)
            if tokenizer.decode([tid]).startswith(' ') and tokenizer.decode([tid]).strip()
        }

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        for beam in range(input_ids.shape[0]):
            top_ids = scores[beam].topk(self.top_k).indices.tolist()
            candidates = [
                (tid, self.tok.decode([tid]).strip().lower())
                for tid in top_ids if tid in self._word_ids
            ]
            if len(candidates) < 2:
                continue

            hyp     = self.tok.decode(input_ids[beam], skip_special_tokens=True)
            context = ' '.join(hyp.strip().lower().split()[-2:])

            lm_scores = [
                (tid, self.lm.score((context + ' ' + w).strip(), bos=not bool(context), eos=False))
                for tid, w in candidates
            ]
            mean_sc = sum(s for _, s in lm_scores) / len(lm_scores)
            for tid, s in lm_scores:
                scores[beam, tid] += self.weight * (s - mean_sc)

        return scores


class VocabConstraintProcessor(LogitsProcessor):
    def __init__(self, tokenizer, dataset_path: str):
        import json
        texts = [d['text'] for d in json.load(open(dataset_path)) if d.get('text')]
        allowed = set()
        for text in texts:
            ids = tokenizer.encode(text, add_special_tokens=False)
            allowed.update(ids)
        for tid in range(TIMESTAMP_BEGIN):
            decoded = tokenizer.decode([tid])
            if not decoded.strip() or all(c in '.,!?;:\'"()- ' for c in decoded):
                allowed.add(tid)
        for tid in range(TIMESTAMP_BEGIN, tokenizer.vocab_size):
            allowed.add(tid)
        self._allowed = torch.tensor(sorted(allowed), dtype=torch.long)
        self._mask    = None

    def _get_mask(self, vocab_size: int, device) -> torch.BoolTensor:
        if self._mask is None or self._mask.device != device:
            mask = torch.ones(vocab_size, dtype=torch.bool, device=device)
            mask[self._allowed.to(device)] = False
            self._mask = mask
        return self._mask

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        mask = self._get_mask(scores.shape[-1], scores.device)
        scores[:, mask] = float('-inf')
        return scores


def rescore_nbest(
    audio: np.ndarray,
    processor: WhisperProcessor,
    model: WhisperForConditionalGeneration,
    device: str,
    lm: kenlm.Model,
    weight: float = 0.5,
    num_hyps: int = 5,
    temperature: float = 0.2,
) -> tuple[str, list[str]]:
    inputs = processor(audio, sampling_rate=WHISPER_SR, return_tensors='pt',
                       return_attention_mask=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(
            **inputs,
            task='transcribe',
            do_sample=True,
            temperature=temperature,
            top_k=50,
            num_return_sequences=num_hyps,
            no_repeat_ngram_size=3,
            condition_on_prev_tokens=False,
            output_scores=True,
            return_dict_in_generate=True,
        )
    texts    = processor.batch_decode(out.sequences, skip_special_tokens=True)
    acoustic = _sequence_log_probs(out)
    lm_scores = [lm.score(t.strip().lower(), bos=True, eos=True) for t in texts]
    combined  = [acoustic[j] + weight * lm_scores[j] for j in range(len(texts))]
    best_j    = max(range(len(texts)), key=lambda j: combined[j])
    return texts[best_j].strip().lower(), [t.strip().lower() for t in texts]


def _sequence_log_probs(out) -> list[float]:
    scores     = out.scores
    seqs       = out.sequences
    prompt_len = seqs.shape[1] - len(scores)
    log_probs  = torch.zeros(seqs.shape[0], device=seqs.device)
    for step, score in enumerate(scores):
        lp    = F.log_softmax(score, dim=-1)
        token = seqs[:, prompt_len + step]
        log_probs += lp.gather(1, token.unsqueeze(1)).squeeze(1)
    return log_probs.tolist()
