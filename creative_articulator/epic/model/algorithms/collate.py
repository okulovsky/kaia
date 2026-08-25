from .text_fragment import TextFragment, Match
from ..basics import hamming_distance

DEFAULT_MIN_MATCH = 0.5

_MAX_LEVENSHTEIN_LENGTH = 5000


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current_row = [i]
        for j, char_b in enumerate(b, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            substitute_cost = previous_row[j - 1] + (char_a != char_b)
            current_row.append(min(insert_cost, delete_cost, substitute_cost))
        previous_row = current_row
    return previous_row[-1]


def similarity(incoming: TextFragment, base: TextFragment) -> float:
    a = incoming.paragraphs.text
    b = base.paragraphs.text
    if a == b:
        return 1.0
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    if longest > _MAX_LEVENSHTEIN_LENGTH:
        return 1.0 - hamming_distance(incoming.paragraphs.simhash, base.paragraphs.simhash) / 64
    return 1.0 - _levenshtein(a, b) / longest


def collate(incoming: tuple[TextFragment,...], base: tuple[TextFragment,...], min_match: float = DEFAULT_MIN_MATCH):
    # Alike to existing collate
    # Must find the best match between old and new
    # After this method, in incoming AND base, the matches should be assigned (if they exist. If not, the field should be left empty)
    for fragment in tuple(incoming) + tuple(base):
        fragment.match = None

    candidates = []
    for i, incoming_fragment in enumerate(incoming):
        incoming_length = len(incoming_fragment.paragraphs.text)
        for j, base_fragment in enumerate(base):
            base_length = len(base_fragment.paragraphs.text)
            longest = max(incoming_length, base_length)
            if longest > 0 and min(incoming_length, base_length) / longest < min_match:
                continue
            value = similarity(incoming_fragment, base_fragment)
            if value >= min_match:
                candidates.append((value, i, j))
    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1], candidate[2]))

    matched_incoming = set()
    matched_base = set()
    for value, i, j in candidates:
        if i in matched_incoming or j in matched_base:
            continue
        incoming[i].match = Match(base[j], value)
        base[j].match = Match(incoming[i], value)
        matched_incoming.add(i)
        matched_base.add(j)
