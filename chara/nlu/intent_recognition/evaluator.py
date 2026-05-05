from collections import Counter
from .chroma_store import IntentStore
from .dataset import IntentUtterance


class IntentEvaluator:
    def __init__(self, store: IntentStore):
        self.store = store

    def classify(self, text: str, k: int = 5, threshold: float | None = None) -> str | None:
        """KNN majority vote over neighbors within threshold. Returns None if none pass."""
        neighbors = self.store.query(text, k=k)
        if not neighbors:
            return None
        if threshold is not None:
            neighbors = [n for n in neighbors if n['distance'] <= threshold]
        if not neighbors:
            return None
        votes = Counter(n['intent'] for n in neighbors)
        return votes.most_common(1)[0][0]

    def evaluate(
        self,
        test: list[IntentUtterance],
        k: int = 5,
        threshold: float | None = None,
    ) -> dict:
        """Evaluates accuracy and per-intent metrics on test set."""
        correct = 0
        total = 0
        per_intent_correct = Counter()
        per_intent_total = Counter()
        rejected = 0

        for u in test:
            predicted = self.classify(u.text, k=k, threshold=threshold)
            per_intent_total[u.intent] += 1
            total += 1
            if predicted is None:
                rejected += 1
            elif predicted == u.intent:
                correct += 1
                per_intent_correct[u.intent] += 1

        accuracy = correct / total if total > 0 else 0.0
        per_intent = {
            intent: {
                'correct': per_intent_correct[intent],
                'total': count,
                'accuracy': per_intent_correct[intent] / count if count > 0 else 0.0,
            }
            for intent, count in per_intent_total.items()
        }

        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'rejected': rejected,
            'per_intent': per_intent,
        }

    def evaluate_negatives(
        self,
        negatives: list[str],
        k: int = 5,
        threshold: float | None = None,
    ) -> dict:
        """Evaluates what % of negatives are rejected (classified as None)."""
        rejected = 0
        predictions = Counter()

        for text in negatives:
            predicted = self.classify(text, k=k, threshold=threshold)
            if predicted is None:
                rejected += 1
            else:
                predictions[predicted] += 1

        total = len(negatives)
        return {
            'total': total,
            'rejected': rejected,
            'rejection_rate': rejected / total if total > 0 else 0.0,
            'false_positives': dict(predictions),
        }
