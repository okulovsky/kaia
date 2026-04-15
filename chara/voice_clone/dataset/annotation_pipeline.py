from ...common import ICache, FileCache, logger, LabelAnnotationCache, AnnotationUnit, TextLabelAnnotator
from .algorithm import AnnotatedSentence, AlgorithmData, Algorithm, build_statistics_plot
from pathlib import Path

class AnnotationCacheData(ICache[list[AnnotatedSentence]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.tasks = FileCache[list[AnnotatedSentence]]()
        self.annotation = LabelAnnotationCache()


class AnnotationPipeline:
    def __init__(self, samples_per_run: int = 100, banned_words: set[str] = ()):
        self.samples_per_run = samples_per_run
        self.banned_words = set(banned_words)

    def __call__(self,
                 cache: AnnotationCacheData,
                 data: AlgorithmData,
                 prior_result: list[AnnotatedSentence]) -> list[AnnotatedSentence]:
        prior_annotation: list[AnnotatedSentence] = prior_result

        @logger.phase(cache.tasks)
        def _():
            algorithm = Algorithm(data)
            result = algorithm.run(
                self.samples_per_run,
                [t.id for t in prior_annotation if not t.accepted],
                [t.id for t in prior_annotation if t.accepted],
                self.banned_words
            )
            logger.log(f"{len(result)} is produced by an algorithm")

            logger.log(build_statistics_plot(data, result))
            cache.tasks.write(result)

        tasks = cache.tasks.read()

        @logger.phase(cache.annotation)
        def _():
            annotation_task = {t.id: t.text for t in tasks}
            unit = AnnotationUnit(TextLabelAnnotator(
                annotation_task,
                TextLabelAnnotator.Settings(("Yes", "No"), "Skip")
            ))
            unit.run(cache.annotation)

        annotation = cache.annotation.get_result()
        for t in tasks:
            if t.id in annotation:
                t.accepted = annotation[t.id] == 'Yes'

        return [t for t in tasks if t.accepted is not None]








