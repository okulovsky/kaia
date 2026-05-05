from typing import Iterable, Callable
from .algorithm import AlgorithmData, Algorithm, build_statistics_plot
from chara import Chara, logger, TextLabelAnnotator, AnnotationPipeline, LabelAnnotatorSettings, CaseCollection
from .common import AnnotationCase

def _get_text(case: AnnotationCase):
    return case.text

def algorithm_annotation_step(
        data: AlgorithmData,
        prior_annotations: list[AnnotationCase],
        lines_per_iteration: int = 100,
        banned_words: Iterable[str] = (),
        mock_annotation: Callable[[AnnotationCase], str]|None = None
) -> tuple[AnnotationCase,...]:

    @Chara.phase
    def running_algorithm():
        algorithm = Algorithm(data)
        result = algorithm.run(
            lines_per_iteration,
            [t.id for t in prior_annotations if not t.accepted],
            [t.id for t in prior_annotations if t.accepted],
            set(banned_words)
        )
        logger.log(f"{len(result)} is produced by an algorithm")

        logger.log(build_statistics_plot(data, result))
        return result

    algorithm_result: list[AnnotationCase] = Chara.previous.result
    settings = LabelAnnotatorSettings(
        ('YES', 'NO'),
        'SKIP'
    )
    annotator = TextLabelAnnotator(_get_text, settings, mock_annotation = mock_annotation)
    pipeline = AnnotationPipeline(annotator)
    annotated = Chara.call(pipeline.__call__)(CaseCollection(algorithm_result))
    return annotated.successes





