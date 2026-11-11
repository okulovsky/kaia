import tempfile
import unittest
from pathlib import Path

import torch
from chara.wakeword.training.checkpoints import (
    candidate_gate,
    choose_candidates,
    select_state,
)
from chara.wakeword.training.state import save_state


class SelectionTests(unittest.TestCase):
    def test_gate(self):
        history = [{"n_fp": n, "recall": r} for n, r in [(4, 0.7), (2, 0.8), (1, 0.9)]]
        self.assertFalse(candidate_gate(history[:2]))
        self.assertTrue(candidate_gate(history))

    def test_fallback(self):
        self.assertEqual(choose_candidates([])[1], "no_candidates_last_trained")
        candidates = [
            {
                "checkpoint_id": str(i),
                "accuracy": a,
                "recall": r,
                "window_fp_per_hour": f,
                "validation_event_id": i,
            }
            for i, a, r, f in [(1, 0.9, 0.1, 5), (2, 0.1, 0.9, 1), (3, 0.1, 0.9, 1)]
        ]
        selected, reason, _ = choose_candidates(candidates)
        self.assertEqual(selected[0]["checkpoint_id"], "2")
        self.assertEqual(reason, "empty_percentile_intersection")

    def test_tensor_averaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = []
            for index, value in enumerate((2.0, 4.0)):
                name = f"{index}.pt"
                save_state(root / name, {"weight": torch.tensor([value])})
                candidates.append(
                    {
                        "checkpoint_id": str(index),
                        "path": name,
                        "accuracy": 0.5,
                        "recall": 0.5,
                        "window_fp_per_hour": 0,
                        "validation_event_id": index,
                    }
                )
            state = select_state(root, candidates)
            self.assertEqual(state["weight"].item(), 3.0)
