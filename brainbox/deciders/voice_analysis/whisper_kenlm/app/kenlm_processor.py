import torch
from transformers import LogitsProcessor

TIMESTAMP_BEGIN = 50364


class KenLMLogitsProcessor(LogitsProcessor):
    def __init__(self, lm, tokenizer, weight: float = 0.5, top_k: int = 50):
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
