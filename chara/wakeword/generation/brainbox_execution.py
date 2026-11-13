"""BrainBoxCasePipeline with persisted task identities and safe resubmission."""

import time
from pathlib import Path
from types import SimpleNamespace

from chara import BrainBoxCasePipeline, CaseCollection, Chara

from .io import read_json, write_json


class DurableCasePipeline(BrainBoxCasePipeline):
    def __call__(self, cases):
        active = cases.clone().successes
        if not active:
            return CaseCollection([], cases.errors)
        folder = Chara.current.folder
        api = Chara.Apis.brainbox_api
        if self.uploader is not None:
            self.uploader.upload(active)
        descriptions = self._build_descriptions(active)
        ids = [job.id for job in descriptions]
        batch_id = self._persist_batch(folder, ids)
        existing, missing = self._find_existing(api, descriptions)
        for job in missing:
            job.batch = batch_id
        self._submit_missing(api, missing)
        # Older saved runs may contain jobs assigned to a shared legacy batch.
        # Poll those jobs directly rather than waiting for unrelated legacy jobs.
        tracked = bool(missing) or any(
            getattr(job, "batch", None) == batch_id for job in existing
        )
        jobs = self._wait_for_results(api, ids, batch_id if tracked else None)
        return self._apply_results(cases, active, folder, api, ids, jobs)

    def _apply_results(self, cases, active, folder, api, ids, jobs):
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

    def _build_descriptions(self, active):
        descriptions = []
        for case in active:
            task = self.task_builder(case)
            request = task.to_job_request()
            if len(request.jobs) != 1 or request.jobs[0].dependencies:
                raise ValueError("durable case stage requires one independent task")
            if not task.optionals.id or request.jobs[0].id != task.optionals.id:
                raise ValueError("task identity must be persisted before submission")
            descriptions.append(request.jobs[0])
        if len({job.id for job in descriptions}) != len(descriptions):
            raise ValueError("duplicate task identities in batch")
        return descriptions

    @staticmethod
    def _persist_batch(folder, ids):
        from uuid import uuid4

        path = folder / "tasks.json"
        previous = read_json(path) if path.exists() else {"ids": ids}
        if previous["ids"] != ids:
            raise ValueError("cached task identity mismatch")
        if not previous.get("batch_id"):
            previous["batch_id"] = "wakeword-" + uuid4().hex
            write_json(path, previous)
        return previous["batch_id"]

    @staticmethod
    def _find_existing(api, descriptions):
        existing, missing = [], []
        for description in descriptions:
            try:
                existing.append(api.jobs.get_job(description.id))
            except Exception as error:
                expected = "Can't find a job with id " + description.id
                if expected not in str(error):
                    raise RuntimeError(
                        "cannot establish task state; refusing synthesis"
                    ) from error
                missing.append(description)
        return existing, missing

    @staticmethod
    def _submit_missing(api, descriptions):
        if not descriptions:
            return
        try:
            api.jobs.base_add(descriptions)
        except Exception:  # noqa: BLE001 - A lost response must be reconciled without duplicate submission.
            # The transaction may have committed despite the lost HTTP response.
            # Never retry this submission blindly, even if only some IDs are visible.
            list(api.jobs.get_jobs([job.id for job in descriptions]))

    @staticmethod
    def _wait_for_results(api, ids, batch_id):
        while True:
            if batch_id is not None:
                progress = api.batches.get_batch_progress(batch_id)
                if not progress.is_finished:
                    time.sleep(1)
                    continue
            records = list(api.jobs.get_jobs(ids))
            jobs = {job.id: job for job in records}
            if len(records) != len(ids) or set(jobs) != set(ids):
                raise RuntimeError(
                    "BrainBox returned incomplete or duplicate task results"
                )
            if all(job.finished for job in records):
                return jobs
            time.sleep(1)
