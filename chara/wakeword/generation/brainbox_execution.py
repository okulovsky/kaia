"""BrainBoxCasePipeline with persisted task identities and safe resubmission."""

import time
from pathlib import Path
from types import SimpleNamespace

from chara import BrainBoxCasePipeline, CaseCollection, Chara

from .io import read_json, write_json


class DurableCasePipeline(BrainBoxCasePipeline):
    def __call__(self, cases):
        active = cases.clone().successes
        folder = Chara.current.folder
        api = Chara.Apis.brainbox_api
        if self.uploader is not None:
            self.uploader.upload(active)
        tasks = [self.task_builder(case) for case in active]
        descriptions = []
        ids = []
        for task in tasks:
            request = task.to_job_request()
            if len(request.jobs) != 1 or request.jobs[0].dependencies:
                raise ValueError("durable case stage requires one independent task")
            job = request.jobs[0]
            if not task.optionals.id:
                raise ValueError("task identity must be persisted before submission")
            job.batch = job.batch or "wakeword-" + folder.name
            descriptions.append(job)
            ids.append(job.id)
        state = folder / "tasks.json"
        if state.exists():
            if read_json(state)["ids"] != ids:
                raise ValueError("cached task identity mismatch")
        else:
            write_json(state, {"ids": ids})
        for description in descriptions:
            try:
                api.jobs.get_job(description.id)
                continue
            except Exception as error:
                # Only the explicit not-found response permits submission.
                expected = "Can't find a job with id " + description.id
                if expected not in str(error):
                    raise RuntimeError(
                        "cannot establish task state; refusing synthesis"
                    ) from error
            try:
                api.jobs.base_add([description])
            except Exception:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
                # A lost response may follow a successful commit. Query the SAME id.
                api.jobs.get_job(description.id)
        pending = set(ids)
        jobs = {}
        while pending:
            for task_id in tuple(pending):
                job = api.jobs.get_job(task_id)
                if job.finished:
                    jobs[task_id] = job
                    pending.remove(task_id)
            if pending:
                time.sleep(1)
        results = []
        files = folder / "files"
        files.mkdir(exist_ok=True)
        for task_id in ids:
            job = jobs[task_id]
            result = job.result
            if job.error is None and self.result_to_file:
                if not isinstance(result, str) or Path(result).name != result:
                    raise ValueError("invalid BrainBox cache name")
                path = files / result
                if not path.exists():
                    temporary = path.with_suffix(path.suffix + ".partial")
                    with temporary.open("wb") as stream:
                        for chunk in api.cache.open(result):
                            stream.write(chunk)
                    temporary.replace(path)
                result = path
            results.append(SimpleNamespace(result=result, error=job.error))
        output = self.result_applicator.apply_iterable_result(active, results)
        return CaseCollection(output, cases.errors)
