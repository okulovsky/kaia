import argparse
from datetime import timedelta
from pathlib import Path

from grammatron import DubParameters
from grammatron.dubs import VariableDub
from grammatron.dubs.implementation.categorical_variable_dub import CategoricalVariableDub
from grammatron.globalization.timedelta_dub import TimedeltaDub
from yo_fluq import FileIO

TIMEDELTA_VALUES = [
    timedelta(minutes=1),
    timedelta(minutes=2),
    timedelta(minutes=3),
    timedelta(minutes=5),
    timedelta(minutes=7),
    timedelta(minutes=10),
    timedelta(minutes=15),
    timedelta(minutes=20),
    timedelta(minutes=25),
    timedelta(minutes=30),
    timedelta(minutes=45),
    timedelta(hours=1),
    timedelta(hours=1, minutes=30),
    timedelta(hours=2),
    timedelta(hours=3),
    timedelta(hours=5),
    timedelta(hours=8),
    timedelta(hours=12),
    timedelta(hours=24),
    timedelta(days=2),
]


def get_values_for_dub(dub, n: int) -> list:
    if isinstance(dub, TimedeltaDub):
        return TIMEDELTA_VALUES[:n]
    if isinstance(dub, CategoricalVariableDub):
        return list(dub.get_values())[:n]
    return []


def expand_record(record, n: int, language: str) -> list[str]:
    try:
        dispatch = record.template.dub.dispatch
        tdub = dispatch.get(record.language) or next(iter(dispatch.values()))
        seq = tdub.sequences[0]
    except (KeyError, IndexError, StopIteration):
        return [record.filename]

    var_dubs = {
        item.name: item.dub
        for item in seq.sequence
        if isinstance(item, VariableDub)
    }

    if not var_dubs:
        return [record.filename]

    value_lists = {name: get_values_for_dub(dub, n) for name, dub in var_dubs.items()}
    valid = {name: vals for name, vals in value_lists.items() if vals}

    if not valid:
        return [record.filename]

    n_actual = min(len(vals) for vals in valid.values())
    results = []
    params = DubParameters(language=language)

    for i in range(n_actual):
        substitution = {name: vals[i] for name, vals in valid.items()}
        try:
            text = record.template.utter(substitution).to_str(params)
            results.append(text)
        except Exception:
            pass

    return results


def main():
    parser = argparse.ArgumentParser(description='Expand dataset: substitute actual values for placeholders')
    parser.add_argument('--input', default='data/result', help='Path to pickle with list[ParaphraseRecord]')
    parser.add_argument('--output', default='data/intent_paraphrases_expanded.txt', help='Output text file path')
    parser.add_argument('--n-values', type=int, default=3, help='Number of different values per variable')
    parser.add_argument('--language', default='ru', help='Rendering language')
    parser.add_argument('--negatives-input', default=None, help='Optional path to negatives text file to append')
    args = parser.parse_args()

    records = FileIO.read_pickle(args.input)
    lines = []

    for record in records:
        lines.append(f"# {record.original_template_name} | {record.language}")
        expanded = expand_record(record, args.n_values, args.language)
        lines.extend(expanded)
        lines.append("")

    negatives_count = 0
    if args.negatives_input:
        neg_path = Path(args.negatives_input)
        if neg_path.exists():
            neg_lines = [l.strip() for l in neg_path.read_text(encoding='utf-8').splitlines() if l.strip()]
            lines.append(f"# __negatives__ | {args.language}")
            lines.extend(neg_lines)
            lines.append("")
            negatives_count = len(neg_lines)

    output = Path(args.output)
    output.write_text('\n'.join(lines), encoding='utf-8')
    text_lines = [l for l in lines if l and not l.startswith('#')]
    print(f"Done. {len(records)} records → {len(text_lines) - negatives_count} sentences"
          + (f" + {negatives_count} negatives" if negatives_count else "")
          + f" → {output}")


if __name__ == '__main__':
    main()
