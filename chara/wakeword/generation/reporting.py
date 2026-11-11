from collections import Counter
from pathlib import Path

from chara import logger

from .io import read_json, write_json
from .settings import GROUPS


def write_report(root, data):
    root = Path(root)
    rejected = {}
    reasons = Counter()
    for path in (root / "review").glob("*/record.json"):
        record = read_json(path)
        rejected[record["sample_id"]] = record
        reasons[record["reason_code"]] += 1
    summary = {}
    for group in GROUPS:
        path = root / "generation_state" / group / "progress.json"
        if not path.exists():
            continue
        progress = read_json(path)
        attempts = progress["attempts"]
        accepted = sum(
            a.get("state") == "accepted" and a["sample_id"] not in rejected
            for a in attempts
        )
        summary[group] = {
            "target": progress["target"],
            "budget": 3 * progress["target"],
            "attempts": len(attempts),
            "accepted": accepted,
            "review": sum(a["sample_id"] in rejected for a in attempts),
        }
    data = dict(data, summary=summary, rejection_reasons=dict(reasons))
    write_json(root / "report.json", data)
    logger.info(
        f"Wakeword run: {data['status']}; {len(rejected)} review records; {root}"
    )
    return data
