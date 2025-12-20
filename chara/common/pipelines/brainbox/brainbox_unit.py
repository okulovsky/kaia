from ...pipelines import logger
from .stats import *
from typing import Callable, Iterable
from brainbox import BrainBox
from .cache import BrainBoxCache, TCase, TOption, BrainBoxUnitResultItem, BrainBoxUnitResultOption
from brainbox.deciders import Collector
from tqdm import tqdm
import time
from itertools import tee
from ..apis import CharaApis

def _default_divide(x):
    return [x]

def _default_merge(x, y):
    return y

def _default_builder(x):
    return x

class BrainBoxUnit(Generic[TCase, TOption]):
    def __init__(self,
                 task_builder: Callable[[TCase], BrainBox.ITask]|None = None,
                 merger: Callable[[TCase, Any], TOption] | None = None,
                 divider: Callable[[Any], list] | None = None,
                 options_as_files: bool = False,
                 ):
        self.task_builder = task_builder if task_builder is not None else _default_builder
        self.merger = merger if merger is not None else _default_merge
        self.divider = divider if divider is not None else _default_divide
        self.options_as_files: bool = options_as_files

    def _match_tasks(self,
                     cases,
                     brainbox_collective_result: dict,
                     task_objects: list[BrainBox.ITask],
                     stats: BrainBoxStats) -> Iterable[BrainBoxUnitResultItem]:
        index_to_result = {}
        for item in brainbox_collective_result:
            index_to_result[item['tags']['index']] = item

        for index, case in enumerate(cases):
            stats.cases_total += 1
            merge = BrainBoxUnitResultItem(case, task_objects[index])
            if index not in index_to_result:
                merge.brainbox_answer_is_missing = True
                stats.cases_missing_from_brainbox += 1
            elif index_to_result[index]['error'] is not None:
                merge.brainbox_error = index_to_result[index]['error']
                stats.cases_with_brainbox_errors += 1
            else:
                merge.brainbox_result = index_to_result[index]['result']
                self._perform_merge(merge, stats)
            yield merge

    def _perform_merge(self, merge: BrainBoxUnitResultItem, stats: BrainBoxStats):
        try:
            brainbox_options = self.divider(merge.brainbox_result)
        except Exception as e:
            merge.divider_error = e
            stats.cases_with_divider_errors += 1
            return

        stats.cases_success += 1

        merge.options = []
        for brainbox_option in brainbox_options:
            stats.options_total += 1
            option = BrainBoxUnitResultOption(brainbox_option)
            try:
                option.option = self.merger(merge.case, brainbox_option)
                stats.options_success += 1
            except Exception as exception:
                option.merge_error = exception
                stats.options_with_errors += 1
            merge.options.append(option)


    def _get_status(self, brainbox_api: BrainBox.Api, task_id: str):
        summary = brainbox_api.summary([task_id])
        if summary[0]['finished']:
            return 1
        return brainbox_api.batch_progress(task_id)['progress']

    def _wait_for_brainbox(self, name: str, task_id: str):
        progress = self._get_status(CharaApis.brainbox_api, task_id)
        with tqdm(total=1.0, initial=progress, desc=name, ncols=100) as pbar:
            while progress < 1.0:
                time.sleep(1)
                new_progress = self._get_status(CharaApis.brainbox_api, task_id)
                new_progress = max(progress, min(1.0, new_progress))
                pbar.update(new_progress - progress)
                progress = new_progress

    def run(self,
            cache: BrainBoxCache,
            cases: Iterable[TCase],
            ):
        cases_1, cases_2 = tee(cases)

        @logger.phase(cache.tasks, "Creating tasks")
        def _():
            tasks = [self.task_builder(case) for case in cases_1]
            cache.tasks.write(tasks)

        tasks = cache.tasks.read()

        @logger.phase(cache.task_id, "Running tasks and waiting for the results")
        def _():
            builder = Collector.TaskBuilder()
            for index, task in enumerate(tasks):
                builder.append(task, dict(index=index))
            task = builder.to_collector_pack('to_array')
            task_id = CharaApis.brainbox_api.add(task)
            cache.task_id.write(task_id)



        @logger.phase(cache.result, "Merging the results")
        def _():
            stats = BrainBoxStats()
            task_id = cache.task_id.read()
            self._wait_for_brainbox(cache.task_id.read(), task_id)
            result = CharaApis.brainbox_api.join(task_id)
            with cache.result.session():
                for merge in self._match_tasks(cases_2, result, tasks, stats):
                    cache.result.write(merge)
            logger.log(stats)

        if self.options_as_files:
            @logger.phase(cache.files, "Downloading files")
            def _():
                for option in cache.read_options():
                    cache.files.write(CharaApis.brainbox_api.open_file(option))
                cache.files.finalize()
        cache.files.finalize()
        cache.finalize()

