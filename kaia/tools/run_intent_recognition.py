from collections import Counter
from foundation_kaia.misc import Loc
from chara.intent_recognition import load_dataset, train_test_split
from chara.intent_recognition.dataset import load_negatives
from brainbox.deciders.utils.chroma.api import ChromaApi, Chroma

K = 3
THRESHOLD = 0.3
TEST_RATIO = 0.2

controller = Chroma.Controller()
controller.run()

try:
    utterances = load_dataset(Loc.data_folder / 'intent_paraphrases_expanded.txt')
    train, test = train_test_split(utterances, test_ratio=TEST_RATIO)

    print(f"Dataset: {len(utterances)} utterances, {len(set(u.intent for u in utterances))} intents")
    print(f"Train: {len(train)}, Test: {len(test)}")
    print()

    api = ChromaApi(controller.address)
    api.train([{'text': u.text, 'intent': u.intent, 'language': u.language} for u in train])


    def classify(text: str) -> str | None:
        neighbors = api.find_neighbors(text, k=K)
        filtered = [n for n in neighbors if n['distance'] <= THRESHOLD]
        if not filtered:
            return None
        return Counter(n['intent'] for n in filtered).most_common(1)[0][0]


    correct = rejected = 0
    per_intent_correct: Counter = Counter()
    per_intent_total: Counter = Counter()

    for u in test:
        predicted = classify(u.text)
        per_intent_total[u.intent] += 1
        if predicted is None:
            rejected += 1
        elif predicted == u.intent:
            correct += 1
            per_intent_correct[u.intent] += 1

    total = len(test)
    print(f"=== Results (K={K}, threshold={THRESHOLD}) ===")
    print(f"Accuracy: {correct / total:.2%}")
    print(f"Correct: {correct}/{total}, Rejected: {rejected}")
    print()
    print("Per intent:")
    for intent, cnt in sorted(per_intent_total.items()):
        c = per_intent_correct[intent]
        print(f"  {intent}: {c}/{cnt} ({c/cnt:.0%})")

    negatives_path = Loc.data_folder / 'negatives.txt'
    if negatives_path.exists():
        negatives = load_negatives(negatives_path)
        neg_rejected = sum(1 for t in negatives if classify(t) is None)
        print()
        print(f"=== Negatives (K={K}, threshold={THRESHOLD}) ===")
        print(f"Rejection rate: {neg_rejected / len(negatives):.2%} ({neg_rejected}/{len(negatives)})")

finally:
    controller.stop_all()
