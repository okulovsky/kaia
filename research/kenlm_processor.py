import kenlm
import torch
from transformers import LogitsProcessor, WhisperTokenizer


class KenLMLogitsProcessor(LogitsProcessor):
    """
    Injects KenLM n-gram scores into Whisper logits at word boundaries.

    At each decode step, for every beam, finds candidate tokens that start
    a new word and adds weight * KenLM_score to their logit. Only text
    tokens (ids < 50364) at word boundaries are modified.
    """

    TIMESTAMP_BEGIN = 50364

    def __init__(self, lm_path: str, tokenizer: WhisperTokenizer, weight: float = 0.5):
        self.lm = kenlm.Model(lm_path)
        self.tokenizer = tokenizer
        self.weight = weight
        self._ids, self._words = self._word_boundary_tokens(tokenizer)

    @staticmethod
    def _word_boundary_tokens(tokenizer: WhisperTokenizer):
        ids, words = [], []
        for tid in range(KenLMLogitsProcessor.TIMESTAMP_BEGIN):
            decoded = tokenizer.decode([tid])
            if decoded.startswith(' ') and decoded.strip():
                ids.append(tid)
                words.append(decoded.strip().lower())
        return ids, words

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        for beam in range(input_ids.shape[0]):
            hyp = self.tokenizer.decode(input_ids[beam], skip_special_tokens=True)
            context_words = hyp.strip().lower().split()
            context = ' '.join(context_words[-2:])

            for tid, word in zip(self._ids, self._words):
                text = (context + ' ' + word).strip() if context else word
                lm_score = self.lm.score(text, bos=not bool(context_words), eos=False)
                scores[beam, tid] += self.weight * lm_score

        return scores
