from .case import DatasetImageCase
from .upscale import upscale
from chara import CaseCollection, AnnotationPipeline, Chara, logger, BrainBoxCasePipeline
from .cropping import CropAnnotator
from .tagging import TagAnnotator
from pathlib import Path
from brainbox.deciders import WD14Tagger
from brainbox import BrainBox


def _case_to_file(case: DatasetImageCase) -> Path:
    return case.source

def _case_to_tagging_task(case: DatasetImageCase) -> BrainBox.Task:
    return WD14Tagger.new_task().interrogate(case.upscaled_local_path.name)

def dataset_pipeline(source_path: Path) -> CaseCollection[DatasetImageCase]:
    raw_cases = []
    for file in sorted(source_path.glob('*.png')):
        raw_cases.append(DatasetImageCase(source=file))
    cases = CaseCollection[DatasetImageCase](raw_cases)

    crop_annotator = CropAnnotator(_case_to_file)
    crop_pipeline = AnnotationPipeline(crop_annotator, 'crop')
    cases: CaseCollection[DatasetImageCase] = Chara.call(crop_pipeline)(cases)
    logger.log(f"{len(cases.errors)} skipped, {len(cases.successes)} active")

    cases = Chara.call(upscale)(cases.successes_collection)

    pipe = BrainBoxCasePipeline(_case_to_tagging_task, 'auto_tags')
    cases = Chara.call(pipe.__call__, 'auto_tagging')(cases).successes_collection

    all_tags = Chara.call(Chara.Apis.brainbox_api.execute, 'all_tags')(WD14Tagger.new_task().tags())
    all_tags = [t['name'] for t in all_tags]


    tag_annotator = TagAnnotator(all_tags, lambda case: case.upscaled_local_path)
    tag_pipeline = AnnotationPipeline(tag_annotator, 'tag_annotation')
    cases = Chara.call(tag_pipeline)(cases)

    return cases

