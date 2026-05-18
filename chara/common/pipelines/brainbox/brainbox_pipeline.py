import os
from brainbox import BrainBox
from typing import Any, Callable, TypeAlias, Iterable
from uuid import uuid4
from ...architecture import Chara, logger
from tqdm import tqdm
import time
import tarfile
from dataclasses import dataclass
from pathlib import Path
import pickle
import io
from yo_fluq import Queryable

ResultToFiles: TypeAlias = bool|Callable[[Any], str|list[str]]|None

@dataclass
class BrainBoxResultItem:
    task_id: str
    task_info: Any
    result: Any
    error: str|None

@dataclass
class BrainBoxStats:
    total: int
    successes: int

class BrainBoxResult:
    def __init__(self, path: Path):
        self.path = path

    def _base_read(self):
        with tarfile.open(self.path/'items.tar', 'r') as tar:
            for member in tar:
                yield pickle.loads(tar.extractfile(member).read())

    def read_all(self) -> Queryable[BrainBoxResultItem]:
        stats: BrainBoxStats = pickle.loads((self.path/'stats.pkl').read_bytes())
        return Queryable(self._base_read(), stats.total)

    def read_successes(self) -> Queryable[BrainBoxResultItem]:
        stats: BrainBoxStats = pickle.loads((self.path / 'stats.pkl').read_bytes())
        return Queryable(self.read_all().where(lambda z: z.error is None), stats.successes)


def brainbox_pipeline(
        tasks: Iterable[BrainBox.Task],
        result_to_file: ResultToFiles = None,
        remove_resulting_files_from_cache: bool = False,
    ) -> BrainBoxResult:
    @Chara.phase(Chara.ResultType.Json)
    def sending_tasks():
        batch_id = str(uuid4())
        job_descriptions = []
        ids = []

        for task in tasks:
            request = task.to_job_request()
            for job in request.jobs:
                job.batch = batch_id
            if request.jobs[0].id is None:
                request.jobs[0].id = str(uuid4())
            ids.append(request.jobs[0].id)
            job_descriptions.extend(request.jobs)

        Chara.Apis.brainbox_api.jobs.base_add(job_descriptions)
        result = dict(batch_id = batch_id, task_ids = ids)
        logger.info(f"{len(ids)} tasks added")
        return result

    ids_object = Chara.previous.result
    batch_id = ids_object['batch_id']
    task_ids = ids_object['task_ids']

    @Chara.phase
    def collecting_results():
        _wait_for_brainbox(batch_id)
        tar_path = Chara.current.folder / 'items.tar'
        files_folder = Chara.current.folder / 'files'
        os.makedirs(files_folder, exist_ok=True)
        index = 0
        successes = 0
        files_to_download = []
        errors_shown = 0
        with tarfile.open(tar_path, 'w') as tar:
            for job in Chara.Apis.brainbox_api.jobs.get_jobs(task_ids):
                item = _get_result(job, result_to_file, files_folder, files_to_download)
                if item.error is not None and errors_shown < 5:
                    logger.info(f"Error: {item.error}")
                    errors_shown += 1

                data_bytes = pickle.dumps(item)
                info = tarfile.TarInfo(name=f'{index:06d}.pkl')
                info.size = len(data_bytes)
                tar.addfile(info, io.BytesIO(data_bytes))
                index += 1
                if item.error is None:
                    successes += 1
        logger.info(f"BrainBox processed {index} task, of which {successes} successes")
        stats = BrainBoxStats(index, successes)
        (Chara.current.folder/'stats.pkl').write_bytes(pickle.dumps(stats))
        for file in files_to_download:
            (files_folder/file).write_bytes(Chara.Apis.brainbox_api.cache.read(file))
            if remove_resulting_files_from_cache:
                Chara.Apis.brainbox_api.cache.delete(file)
        return None

    return BrainBoxResult(Chara.previous.folder)


def _get_result(job, result_to_file: ResultToFiles, files_folder: Path, files_to_download: list) -> BrainBoxResultItem:
    if job.error is not None:
        return BrainBoxResultItem(job.id, job.info, None, job.error)
    result = job.result
    multifiles, files = _process_files(result_to_file, result)
    if files is not None:
        files_to_download.extend(files)
        paths = [files_folder/file for file in files]
        if multifiles:
            result = paths
        else:
            result = paths[0]
    return BrainBoxResultItem(job.id, job.info, result, None)


def _wait_for_brainbox(batch_id: str):
    progress = Chara.Apis.brainbox_api.batches.get_batch_progress(batch_id)
    value = progress.progress
    sleep_time = 0.01
    with tqdm(total=1.0, initial=value, desc=batch_id, ncols=100, bar_format='{l_bar}{bar}| {n:.2f}/{total:.2f} [{elapsed}<{remaining}]') as pbar:
        while not progress.is_finished:
            time.sleep(sleep_time)
            if sleep_time < 1:
                sleep_time *= 1.5
            new_progress = Chara.Apis.brainbox_api.batches.get_batch_progress(batch_id)
            new_value = new_progress.progress
            new_value = max(value, min(1.0, new_value))
            pbar.update(new_value - value)
            value = new_value
            progress = new_progress


def _process_files(result_to_file: ResultToFiles, value) -> tuple[bool, list[str]|None]:
    if result_to_file is None:
        return False, None
    elif isinstance(result_to_file, bool):
        if isinstance(value, str):
            return False, [value]
        else:
            raise ValueError(f"if result_to_str is True, the brainbox output must be string, but was: {value}")
    elif callable(result_to_file):
        files = result_to_file(value)
        if isinstance(files, str):
            return False, [files]
        try:
            return True, list(files)
        except Exception as e:
            raise ValueError("`result_to_file` must return str or iterable[str]") from e
    else:
        raise ValueError("result_to_file must be None, true or callable, converting the brainbox output to str or list[str]")








