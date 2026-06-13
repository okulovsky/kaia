from .case import DatasetImageCase
from .upscale import upscale
from chara import CaseCollection, AnnotationPipeline, Chara, logger, BrainBoxCasePipeline
from .cropping import CropAnnotator
from .tagging import TagAnnotator
from pathlib import Path
from brainbox.deciders import WD14Tagger
from brainbox import BrainBox
import os
import zipfile
from foundation_kaia.marshalling.serialization import Serializer
import json

def _case_to_file(case: DatasetImageCase) -> Path:
    return case.source

def _case_to_tagging_task(case: DatasetImageCase) -> BrainBox.Task:
    return WD14Tagger.new_task().interrogate(case.upscaled_local_path.name)

def dataset_pipeline(source_path: Path) -> Path:
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

    zip_file_path = Chara.current.folder / 'dataset.zip'
    if zip_file_path.exists():
        os.unlink(zip_file_path)

    serializer = Serializer.parse(DatasetImageCase)
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for case in cases.successes:
            if case.error is not None or case.tag_annotation.rejected:
                continue
            zf.write(case.upscaled_local_path, case.source.name)
            json_name = case.source.name.rsplit('.', 1)[0] + '.json'
            zf.writestr(json_name, json.dumps(serializer.to_json(case)))

    return zip_file_path




