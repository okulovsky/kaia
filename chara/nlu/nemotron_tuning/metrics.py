"""
What happens to the word in the slot and to the words around it.

A made-up word has no single right spelling, so the slot is scored by the character errors and not only by the exact match.
No heavy imports, as in manifest.py.
"""
from collections import defaultdict
import manifest
from manifest import edit_distance

CLOSE = 0.25


def word_error_rate(items: list[dict], texts: list[str]) -> dict:
    """WER in total, per language and per group of the manifest"""
    result = {}
    for key in sorted({i['language'] for i in items} | {i['group'] for i in items if 'group' in i}) + ['all']:
        pairs = [(i, t) for i, t in zip(items, texts) if key in ('all', i['language'], i.get('group'))]
        errors = [manifest.word_errors(i['text'], t) for i, t in pairs]
        result[key] = round(sum(e for e, _ in errors) / max(1, sum(n for _, n in errors)), 4)
    return result


def with_slot(rows: list[dict]) -> list[dict]:
    """The rows of the phrases with a word in the slot: real speech and ordinary phrases have none"""
    return [r for r in rows if r.get('word')]


def slot_result(text: str, word: str, hypothesis: str) -> dict:
    """
    Splits the hypothesis into the words before the slot, the slot and the words after it, so that the errors are the smallest.
    `slot_errors` is the share of the wrong characters of the slot, `neighbour_errors` counts the wrong words around it.
    """
    reference = manifest.normalize(text).split()
    slot = manifest.normalize(word).split()
    start = next(i for i in range(len(reference)) if reference[i:i + len(slot)] == slot)
    before, after = reference[:start], reference[start + len(slot):]
    spoken, written = ''.join(slot), manifest.normalize(hypothesis).split()

    best = None
    for left in range(len(written) + 1):
        for right in range(left, len(written) + 1):
            neighbours = edit_distance(before, written[:left]) + edit_distance(after, written[right:])
            heard = ''.join(written[left:right])
            slot_errors = min(1.0, edit_distance(spoken, heard) / len(spoken))
            if best is None or neighbours + slot_errors < best[0] + best[1]:
                best = neighbours, slot_errors, heard
    return dict(
        slot_errors=best[1],
        slot_exact=best[1] == 0,
        slot_close=best[1] <= CLOSE,
        neighbour_errors=best[0],
        neighbour_words=len(before) + len(after),
        heard=best[2],
    )


def summary(rows: list[dict]) -> dict:
    """Rows are the records of a manifest with `hypothesis`"""
    results = [slot_result(r['text'], r['word'], r['hypothesis']) for r in rows]
    count = max(1, len(rows))
    return dict(
        count=len(rows),
        slot_exact=sum(r['slot_exact'] for r in results) / count,
        slot_close=sum(r['slot_close'] for r in results) / count,
        slot_errors=sum(r['slot_errors'] for r in results) / count,
        neighbour_wer=sum(r['neighbour_errors'] for r in results) / max(1, sum(r['neighbour_words'] for r in results)),
        empty=sum(manifest.normalize(r['hypothesis']) == '' for r in rows) / count,
    )


def table(rows: list[dict]) -> list[str]:
    """By group and language, and by group over all the languages. The rows must have a slot, see with_slot"""
    groups = defaultdict(list)
    for row in rows:
        groups[row['group'], row['language']].append(row)
        groups[row['group'], 'all'].append(row)
    lines = [f"{'group':8} {'language':8} {'n':>4} {'exact':>6} {'close':>6} {'slot err':>8} {'neighb WER':>10} {'empty':>6}"]
    for (group, language), part in sorted(groups.items()):
        s = summary(part)
        lines.append(f"{group:8} {language:8} {s['count']:4} {s['slot_exact']:6.1%} {s['slot_close']:6.1%} "
                     f"{s['slot_errors']:8.3f} {s['neighbour_wer']:10.3f} {s['empty']:6.1%}")
    return lines
