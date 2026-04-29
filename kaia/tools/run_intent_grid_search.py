import time
from collections import Counter
from foundation_kaia.misc import Loc
from chara.intent_recognition import load_dataset, train_test_split
from chara.intent_recognition.dataset import load_negatives
from brainbox.deciders.utils.chroma.api import ChromaApi, Chroma

utterances = load_dataset(Loc.data_folder / 'intent_paraphrases_expanded.txt')
train, test = train_test_split(utterances, test_ratio=0.2)

negatives_path = Loc.data_folder / 'negatives.txt'
negatives = load_negatives(negatives_path) if negatives_path.exists() else []

print(f"Train: {len(train)}, Test: {len(test)}, Negatives: {len(negatives)}")
print()

controller = Chroma.Controller()
controller.run()

try:
    api = ChromaApi(controller.address)
    t0 = time.perf_counter()
    api.train([{'text': u.text, 'intent': u.intent, 'language': u.language} for u in train])
    load_time = time.perf_counter() - t0


    def classify(text: str, k: int, threshold: float | None) -> str | None:
        neighbors = api.find_neighbors(text, k=k)
        filtered = [n for n in neighbors if n['distance'] <= threshold] if threshold is not None else neighbors
        if not filtered:
            return None
        return Counter(n['intent'] for n in filtered).most_common(1)[0][0]


    print(f"{'K':>3} {'threshold':>10} {'accuracy':>10} {'test_rej':>10} {'neg_rej':>10}")
    print("-" * 48)

    query_times = []

    for k in [1, 3, 5, 7, 9]:
        for threshold in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, None]:
            t1 = time.perf_counter()

            correct = rejected_test = 0
            for u in test:
                p = classify(u.text, k, threshold)
                if p is None:
                    rejected_test += 1
                elif p == u.intent:
                    correct += 1

            neg_rejected = sum(1 for t in negatives if classify(t, k, threshold) is None)

            elapsed = time.perf_counter() - t1
            n_queries = len(test) + len(negatives)
            query_times.append(elapsed / n_queries)

            t_str = f"{threshold:.1f}" if threshold is not None else "None"
            neg_rate = neg_rejected / len(negatives) if negatives else 0.0
            print(f"{k:>3} {t_str:>10} {correct / len(test):>9.0%} {rejected_test:>10} {neg_rate:>9.0%}")
        print()

    print(f"Load time:          {load_time:.2f}s")
    print(f"Avg time per query: {sum(query_times)/len(query_times)*1000:.2f}ms")

finally:
    controller.stop_all()
