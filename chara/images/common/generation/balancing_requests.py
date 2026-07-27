import random
from collections import defaultdict
from ..activity import ImageRequest
from .dto import ImageSetupStatistics



def balancing_requests(
        stats: list[ImageSetupStatistics],
        budget: int,
        stratification_fields: tuple[str, ...],
) -> list[ImageRequest]:
    """Picks previously-unprocessed activities so that, after generation, all the
    groups of ImageSetups sharing the same stratification_key are more equally
    represented. Pure function - not a Chara.call, not a pipeline: nothing here is
    worth caching, batching, or retrying.

    Works in rounds: each round, every group currently tied for the fewest generated
    images "deserves" a pick and gets one - a random still-pending activity from a
    random setup within that group. Generated counts are then updated and the
    deserving groups are recomputed for the next round, so a group that just got
    picked immediately falls back in line with the others. If the budget runs out
    before a whole round of deserving groups can be served, which of them get picked
    is randomized too."""

    def total_generated(s: ImageSetupStatistics) -> int:
        return sum(a.generated for a in s.activity_status.values())

    generated = [total_generated(s) for s in stats]
    pending = [[a for a, st in s.activity_status.items() if st.generated == 0] for s in stats]

    groups: dict[tuple, list[int]] = defaultdict(list)
    for i, s in enumerate(stats):
        key = s.setup.to_fingerprint().stratification_key(stratification_fields)
        groups[key].append(i)

    def group_generated(indices: list[int]) -> int:
        return sum(generated[i] for i in indices)

    def group_pending(indices: list[int]) -> list[int]:
        return [i for i in indices if pending[i]]

    requests: list[ImageRequest] = []
    while len(requests) < budget:
        candidates = [key for key, indices in groups.items() if group_pending(indices)]
        if not candidates:
            break

        deserving_level = min(group_generated(groups[key]) for key in candidates)
        deserving = [key for key in candidates if group_generated(groups[key]) == deserving_level]
        random.shuffle(deserving)

        for key in deserving:
            if len(requests) >= budget:
                break
            i = random.choice(group_pending(groups[key]))
            activity = pending[i].pop(random.randrange(len(pending[i])))
            requests.append(ImageRequest(stats[i].setup, activity))
            generated[i] += 1

    return requests
