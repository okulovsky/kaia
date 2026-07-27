import random
from typing import Callable, Any
from brainbox.deciders.images.comfyui.workflows import IWorkflow
from chara.common.tools.llm import QuestionList, PromptTaskBuilder, JinjaPrompter, parse_and_assign_json
from chara import BrainBoxCasePipeline, logger
from ..scenario import IImageScenario
from chara import Chara, CaseCollection, ICase
from dataclasses import dataclass
from brainbox.deciders import Ollama
from pathlib import Path

@dataclass
class VariantCase:
    prompt: str
    image: Path|None = None

@dataclass
class DrawingCase(ICase):
    scenario: IImageScenario
    workflow: IWorkflow = Any
    image: Path|None = None
    review_questions: QuestionList|None = None
    review_answers: dict|None = None
    variants: dict[str, VariantCase]|None = None

@dataclass
class ReviewSetup:
    model: str
    questions: QuestionList
    filtration: Callable[[DrawingCase], str|None]


class DrawingPipeline:
    def __init__(self,
                 review_setup: ReviewSetup|None = None,
                 variant_pipelines: dict[str, Callable[[CaseCollection[DrawingCase]], CaseCollection[DrawingCase]]]|None = None,
                 ):
        self.review_setup = review_setup
        self.variant_pipelines = variant_pipelines if variant_pipelines is not None else {}

        self._inner_review_task_builder = None

    def _create_task(self, case: DrawingCase):
        return case.workflow

    def _review(self, drawing_cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        if self.review_setup is None:
            return drawing_cases

        for case in drawing_cases.cases:
            case.review_questions = self.review_setup.questions

        review_pipeline = BrainBoxCasePipeline(
            PromptTaskBuilder(
                self.review_setup.model,
                JinjaPrompter(Path(__file__).parent / 'review.jinja'),
                options=Ollama.Options(format=self.review_setup.questions.get_format()),
                image_field='image'
            ),
            parse_and_assign_json('review_answers'),
        )

        cases = Chara.call(review_pipeline, 'review')(drawing_cases)

        for case in cases.successes:
            result = self.review_setup.filtration(case)
            if result is not None:
                case.error = result
        return cases

    def _run_variant_pipelines(
            self,
            reviewed_cases: CaseCollection[DrawingCase],
    ) -> CaseCollection[DrawingCase]:
        erroneous = reviewed_cases.errors
        normal = reviewed_cases.successes_collection

        for variant_name, variant_pipeline in self.variant_pipelines.items():
            normal = Chara.call(variant_pipeline, f"Drawing variant {variant_name}")(normal)
            for case in normal.cases:
                case.error = None
            normal = CaseCollection(normal.cases)

        return CaseCollection(erroneous, normal)


    def __call__(self, cases: CaseCollection[IImageScenario]) -> CaseCollection[DrawingCase]:
        drawing_cases_list = []
        for c in cases.successes:
            drawing_case = DrawingCase(c, c.to_workflow())
            drawing_cases_list.append(drawing_case)
        drawing_cases_list = random.sample(drawing_cases_list, len(drawing_cases_list))
        drawing_cases = CaseCollection(drawing_cases_list)
        pipeline = BrainBoxCasePipeline(self._create_task, 'image', result_to_file=True)

        drawing_cases = Chara.call(pipeline,'drawing')(drawing_cases).raise_if_all_errors()

        reviewed_cases = Chara.call(self._review, 'review')(drawing_cases).raise_if_all_errors()

        successes = 0
        errors: dict[str, int] = {}
        for case in reviewed_cases.cases:
            if case.error is None:
                successes += 1
                continue
            err = case.error[:20]
            if err not in errors:
                errors[err] = 0
            errors[err] += 1

        logger.info(f"Successes: {successes}")
        for key, value in errors.items():
            logger.info(f"Error {key}: {value}")

        final_cases = Chara.call(self._run_variant_pipelines)(reviewed_cases)

        return final_cases






