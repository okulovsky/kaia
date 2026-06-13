from copy import deepcopy
from typing import Callable, Generic, Any
from ..cases import TCase, CaseCollection, ICasePipeline
from brainbox import BrainBox
from .brainbox_pipeline import ResultToFiles, brainbox_pipeline
from ...architecture import Chara
import traceback
from .brainbox_case_pipeline_uploader import BrainBoxCasePipelineUploader

class BrainBoxCaseResultApplicator:
    def __init__(self,
                 applicator: Callable[[TCase, Any], None] | str | None,
                 divider: Callable[[Any], list[Any]] | None = None,
                 ):
        self.applicator = applicator
        self.divider = divider

    def _apply(self, case: TCase, result: Any):
        if self.applicator is None:
            return
        if isinstance(self.applicator, str):
            setattr(case, self.applicator, result)
        else:
            try:
                self.applicator(case, result)
            except Exception:
                case.error = "Application error: \n"+traceback.format_exc()

    def _full_apply_one_case(self, output_cases: list, case, result):
        if self.divider is None:
            self._apply(case, result)
            output_cases.append(case)
            return
        else:
            try:
                subresults = self.divider(result)
            except Exception:
                case.error = "Division error: \n" + traceback.format_exc()
                output_cases.append(case)
                return
            for subresult in subresults:
                new_case = deepcopy(case)
                self._apply(new_case, subresult)
                output_cases.append(new_case)


    def apply_brainbox_result(self, cases, results):
        output_cases = []
        for case, result in zip(cases, results.read_all()):
            if result.error is not None:
                case.error = result.error
                output_cases.append(case)
                continue
            self._full_apply_one_case(output_cases, case, result.result)
        return output_cases

    def apply_cached_result(self, cases: CaseCollection, field: str):
        output_cases = []
        for case in cases.cases:
            if case.error is None:
                self._full_apply_one_case(output_cases, case, getattr(case, field))
            else:
                output_cases.append(case)
        return output_cases




class BrainBoxCasePipeline(Generic[TCase], ICasePipeline[TCase]):
    Uploader = BrainBoxCasePipelineUploader

    def __init__(self,
                 task_builder: Callable[[TCase], BrainBox.Task],
                 applicator: Callable[[TCase, Any], None]|str|None,
                 divider: Callable[[Any], list[Any]]|None = None,
                 result_to_file: ResultToFiles = None,
                 uploader: BrainBoxCasePipelineUploader[TCase]|None = None,
                 remove_resulting_files_from_cache: bool = False,
                 ):
        self.task_builder = task_builder
        self.result_applicator = BrainBoxCaseResultApplicator(applicator, divider)
        self.result_to_file = result_to_file
        self.remove_resulting_files_from_cache = remove_resulting_files_from_cache
        self.uploader = uploader




    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        active_cases = cases.clone().successes
        tasks = [self.task_builder(case) for case in active_cases]

        names = None
        if self.uploader is not None:
            names = Chara.call(self.uploader.upload)(active_cases)

        results = Chara.call(brainbox_pipeline)(tasks, self.result_to_file, self.remove_resulting_files_from_cache)
        output_cases = self.result_applicator.apply_brainbox_result(active_cases, results)

        if self.uploader is not None:
            Chara.call(self.uploader.cleanup)(names)

        return CaseCollection(output_cases, cases.errors)









