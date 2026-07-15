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

    root_folder = Chara.current.folder

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
        return result

    algorithm_result: list[AnnotationCase] = Chara.previous.result
    settings = LabelAnnotatorSettings(
        ('YES', 'NO'),
        'SKIP'
    )
    annotator = TextLabelAnnotator(_get_text, settings, mock_annotation = mock_annotation)
    pipeline = AnnotationPipeline(annotator, lambda case, result: case.set_annotation(result[case.get_id()]))
    annotated = Chara.call(pipeline.__call__)(CaseCollection(algorithm_result))
    successes = annotated.successes

    accepted_so_far = [c for c in prior_annotations if c.accepted] + [c for c in successes if c.accepted]
    plot = build_statistics_plot(data, accepted_so_far)
    plot.figure.savefig(root_folder / 'statistics.png', bbox_inches='tight')
    logger.log(plot)

    return successes





