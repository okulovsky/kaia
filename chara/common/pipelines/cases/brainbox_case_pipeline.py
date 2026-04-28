import copy
from copy import deepcopy

from .arch import TCase
from typing import Generic, Callable, Any
from brainbox import BrainBox
from ..brainbox import BrainBoxPipeline, BrainBoxCache
from ..logger_definition import logger
from .arch import CaseCache


class BrainBoxCasePipeline(Generic[TCase]):
    def __init__(self,
                 task_builder: Callable[[TCase], BrainBox.Task],
                 applicator: Callable[[TCase, Any], None],
                 divider: Callable[[Any], Any]|None = None,
                 options_as_files: bool = False,
                 ):
        self.task_builder = task_builder
        self.applicator = applicator
        self.divider = divider
        self.options_as_files = options_as_files


    def __call__(self, cache: CaseCache[TCase], cases: list[TCase]) -> None:
        inner_cache = cache.create_subcache('brainbox', BrainBoxCache[TCase, Any])
        @logger.phase(inner_cache)
        def _():
            pipe = BrainBoxPipeline(self.task_builder, divider = self.divider, options_as_files=self.options_as_files)
            pipe.run(inner_cache, cases)

        if self.divider is None:
            result = self._parse_one_on_one(inner_cache)
        else:
            result = self._parse_one_to_many(inner_cache)
        cache.write_result(result)

    def _use_applicator(self, case: TCase, cache: BrainBoxCache[TCase, Any], option: Any) -> None:
        if self.options_as_files:
            option = cache.files.working_folder/option
        self.applicator(case, option)



    def _parse_one_to_many(self, inner_cache: BrainBoxCache[TCase, Any]) -> list[TCase]:
        result = []
        for case, option in inner_cache.read_cases_and_options():
            case = deepcopy(case)
            self._use_applicator(case, inner_cache, option)
            result.append(case)
        return result


    def _parse_one_on_one(self, inner_cache: BrainBoxCache[TCase, Any]) -> list[TCase]:
        cases = []
        for result in inner_cache.read_result():
            case = result.case
            cases.append(case)

            if result.brainbox_error is not None:
                case.error = result.brainbox_error
                continue
            elif result.brainbox_answer_is_missing:
                case.error = "Case didn't receive the output from BrainBox"
                continue
            elif result.divider_error is not None:
                raise ValueError("`divider` is not set, but divider_error is present")

            if len(result.options) == 0:
                raise ValueError("No error on case side, but options are missing")
            elif len(result.options) > 1:
                raise ValueError("`divider` is not set, but there were multiple options per case")

            option = result.options[0]
            if option.merge_error is not None:
                case.error = option.merge_error
                continue

            self._use_applicator(case, inner_cache, option.option)


        return cases
















