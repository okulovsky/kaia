"""Stable task identity and conservative lost-response reconciliation."""

import json
import time

from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    write_json,
)


class Submission:
    def __init__(self, api, root):
        self.api = api
        self.root = root

    def submit(self, task, identity):
        path = self.root / ("submission-" + identity + ".json")
        if path.exists() and read_json(path)["task_id"] != identity:
            raise ValueError("task identity changed")
        write_json(path, {"task_id": identity})
        try:
            self.api.jobs.get_job(identity)
        except Exception as error:
            if "Can't find a job with id " + identity not in str(error):
                raise RuntimeError(
                    "transport_unknown; cannot establish task state"
                ) from error
            try:
                self.api.add(task)
            except Exception:  # noqa: BLE001 - Reconcile lost response without duplicate training.
                self.api.jobs.get_job(identity)
        return identity

    def follow(self, identity, streamed=False):
        while True:
            job = self.api.jobs.get_job(identity)
            if job.finished:
                break
            time.sleep(1)
        if job.error:
            raise RuntimeError(job.error)
        if not streamed:
            return job.result
        result = None
        for line in self.api.cache.read(job.result).decode("utf-8").splitlines():
            if line.strip():
                event = json.loads(line)
                if event.get("result") is not None:
                    result = event["result"]
        if result is None:
            raise RuntimeError("training returned no result reference")
        return result
