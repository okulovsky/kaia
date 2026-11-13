"""Notebook percentile gates and deterministic checkpoint selection."""

from pathlib import Path

import numpy as np
import torch

from ..generation.io import sha256, write_json
from .state import save_state


def candidate_gate(events):
    return (
        len(events) >= 3
        and events[-1]["n_fp"] <= np.percentile([x["n_fp"] for x in events], 50)
        and events[-1]["recall"] >= np.percentile([x["recall"] for x in events], 5)
    )


def choose_candidates(candidates):
    if not candidates:
        return [], "no_candidates_last_trained", {}
    percentiles = {
        key: float(np.percentile([x[key] for x in candidates], p))
        for key, p in [("accuracy", 90), ("recall", 90), ("window_fp_per_hour", 10)]
    }
    chosen = [
        c
        for c in candidates
        if c["accuracy"] >= percentiles["accuracy"]
        and c["recall"] >= percentiles["recall"]
        and c["window_fp_per_hour"] <= percentiles["window_fp_per_hour"]
    ]
    if chosen:
        return chosen, None, percentiles
    return (
        [
            min(
                candidates,
                key=lambda c: (
                    c["window_fp_per_hour"],
                    -c["recall"],
                    c["validation_event_id"],
                ),
            )
        ],
        "empty_percentile_intersection",
        percentiles,
    )


def select_state(root, candidates):
    root = Path(root)
    chosen, reason, percentiles = choose_candidates(candidates)
    sources = chosen or [{"path": "last-trained.pt"}]
    result = None
    for candidate in sources:
        state = torch.load(
            root / candidate["path"], map_location="cpu", weights_only=True
        )
        if any(not t.is_floating_point() for t in state.values()):
            raise ValueError("integer buffer averaging requires a new policy")
        if result is None:
            result = {k: v.clone() / len(sources) for k, v in state.items()}
        else:
            for k, v in state.items():
                result[k].add_(v / len(sources))
    save_state(root / "final-state.pt", result)
    selection = {
        "policy_version": "percentiles-v1",
        "candidate_ids": [x["checkpoint_id"] for x in candidates],
        "selected_ids": [x["checkpoint_id"] for x in chosen],
        "percentile_values": percentiles,
        "fallback_reason": reason,
        "tie_break": "window_rate,recall,earliest_event",
        "final_state_path": "final-state.pt",
        "final_state_sha256": sha256(root / "final-state.pt"),
    }
    write_json(root / "checkpoint-selection.json", selection)
    return result
