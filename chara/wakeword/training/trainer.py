"""Three-stage notebook curriculum with actual optimizer update history."""

import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from ..generation.io import sha256, write_json
from .batches import row_batches, sample_batch, window_batches
from .checkpoints import candidate_gate
from .metrics import positive_count, valid_scores
from .state import append_event, save_state


def learning_rate(step, steps, base):
    warmup = max(1, steps // 5)
    hold = steps // 3
    if step < warmup:
        return base * (step + 1) / warmup
    if step < warmup + hold:
        return base
    t = (step - warmup - hold) / max(1, steps - warmup - hold)
    return base * 0.5 * (1 + math.cos(math.pi * min(1, t)))


def validation_steps(steps, start_fraction, limit):
    start = min(steps - 1, int(steps * start_fraction))
    return set(
        np.linspace(start, steps - 1, min(limit, steps - start)).astype(int).tolist()
    )


@torch.no_grad()
def measure(model, arrays, snapshot, settings, device):
    model.eval()

    def count(batches):
        n = 0
        for x in batches:
            scores = (
                torch.sigmoid(model(torch.from_numpy(x).to(device)))
                .cpu()
                .numpy()
                .reshape(-1)
            )
            valid_scores(scores)
            n += positive_count(scores, settings.threshold)
        return n

    p = arrays["positive_features_test"]
    n = arrays["negative_features_test"]
    tp = count(row_batches(p, settings.validation_batch_size))
    fp = count(row_batches(n, settings.validation_batch_size))
    bg = snapshot["background"]
    nfp = count(
        window_batches(
            arrays["background_validation"],
            bg["segment_lengths"],
            settings.validation_batch_size,
        )
    )
    model.train()
    return {
        "recall": tp / len(p),
        "accuracy": (tp + len(n) - fp) / (len(p) + len(n)),
        "n_fp": nfp,
        "window_fp_per_hour": nfp / bg["feature_equivalent_hours"],
        "TP": tp,
        "FP": fp,
        "TN": len(n) - fp,
        "FN": len(p) - tp,
        "positive_count": len(p),
        "negative_count": len(n),
        "threshold": settings.threshold,
        "evaluated_windows": bg["total_valid_windows"],
        "feature_equivalent_hours": bg["feature_equivalent_hours"],
    }


def train(model, arrays, snapshot, settings, root, device):
    root = Path(root)
    rng = np.random.default_rng(settings.seed)
    model.to(device)
    model.train()
    started = time.monotonic()
    updates = 0
    iterations = 0
    event_id = 0
    candidates = []
    validations = []
    maximum = settings.max_negative_weight

    def event(kind, stage, step, **values):
        nonlocal event_id
        event_id += 1
        item = dict(
            schema_version=1,
            type=kind,
            event_id=event_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            stage_iteration=step,
            global_iteration=iterations,
            optimizer_update=updates,
            elapsed_seconds=time.monotonic() - started,
            **values,
        )
        append_event(root, item)
        if kind == "validation":
            from chara import logger

            logger.info(
                f"Training stage {stage}, iteration {step}, updates {updates}: recall={values['recall']:.4f}, window rate={values['window_fp_per_hour']:.4f}/h"
            )
        return item

    for stage, (steps, base_lr, start) in enumerate(
        zip(
            settings.stage_steps,
            settings.stage_learning_rates,
            settings.validation_start_fractions,
        ),
        1,
    ):
        optimizer = torch.optim.Adam(model.parameters(), lr=base_lr)
        scheduled = validation_steps(steps, start, settings.validations_per_stage)
        accumulated = []
        skipped = 0
        retained = 0
        stage_updates = updates

        def update(
            step,
            lr,
            weight,
            flush=False,
            accumulated=accumulated,
            optimizer=optimizer,
            stage=stage,
        ):
            nonlocal updates
            if not accumulated:
                return
            logits = torch.cat([x[0] for x in accumulated])
            y = torch.cat([x[1] for x in accumulated])
            w = torch.cat([x[2] for x in accumulated])
            loss = (
                torch.nn.functional.binary_cross_entropy_with_logits(
                    logits, y, reduction="none"
                )
                * w
            ).mean()
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            updates += 1
            if any(not torch.isfinite(p).all() for p in model.parameters()):
                raise ValueError("non-finite model weights")
            event(
                "update",
                stage,
                step,
                weighted_bce_loss=float(loss.detach()),
                learning_rate=lr,
                negative_weight=weight,
                accumulated_examples=len(y),
                positive_examples=int((y == 1).sum()),
                negative_examples=int((y == 0).sum()),
                flush_remainder=flush,
            )
            accumulated.clear()

        for step in range(steps):
            iterations += 1
            lr = learning_rate(step, steps, base_lr)
            weight = 1 + (maximum - 1) * step / max(1, steps - 1)
            for group in optimizer.param_groups:
                group["lr"] = lr
            x, y = sample_batch(arrays, settings, rng)
            x = torch.from_numpy(x).to(device)
            y = torch.from_numpy(y).to(device)
            logits = model(x).squeeze(-1)
            scores = torch.sigmoid(logits)
            if not torch.isfinite(scores).all():
                raise ValueError("non-finite training scores")
            keep = ((y == 0) & (scores >= 0.001)) | ((y == 1) & (scores < 0.999))
            if int(keep.sum()):
                k = logits[keep]
                labels = y[keep]
                w = torch.where(
                    labels > 0.5,
                    torch.ones_like(labels),
                    torch.full_like(labels, weight),
                )
                accumulated.append((k, labels, w))
                retained += len(k)
            else:
                skipped += 1
            if sum(len(x[0]) for x in accumulated) >= settings.accumulation_examples:
                update(step + 1, lr, weight)
            if step == steps - 1:
                update(step + 1, lr, weight, flush=True)
            if step in scheduled:
                measured = measure(model, arrays, snapshot, settings, device)
                validations.append(measured)
                candidate = None
                if candidate_gate(validations):
                    cid = f"validation-{len(validations):04d}"
                    path = f"checkpoints/{cid}.pt"
                    save_state(
                        root / path,
                        {
                            k: v.detach().cpu().clone()
                            for k, v in model.state_dict().items()
                        },
                    )
                    candidate = dict(
                        checkpoint_id=cid,
                        path=path,
                        sha256=sha256(root / path),
                        validation_event_id=event_id + 1,
                        stage=stage,
                        global_iteration=iterations,
                        optimizer_update=updates,
                        **measured,
                    )
                    candidates.append(candidate)
                    write_json(root / "checkpoints/index.json", candidates)
                event(
                    "validation",
                    stage,
                    step + 1,
                    checkpoint_candidate_id=candidate["checkpoint_id"]
                    if candidate
                    else None,
                    **measured,
                )
        if (
            stage < 3
            and min(x["window_fp_per_hour"] for x in validations)
            > settings.target_window_fp_per_hour
        ):
            maximum *= 2
        event(
            "stage_end",
            stage,
            steps,
            sampled_iterations=steps,
            optimizer_updates=updates - stage_updates,
            skipped_iterations=skipped,
            retained_examples=retained,
            next_negative_weight_max=maximum,
        )
    if not updates:
        raise ValueError("zero optimizer updates; training is not complete")
    save_state(
        root / "last-trained.pt",
        {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
    )
    write_json(root / "checkpoints/index.json", candidates)
    return {
        "optimizer_updates": updates,
        "sampling_iterations": iterations,
        "elapsed_seconds": time.monotonic() - started,
    }
