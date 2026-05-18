from .case import DatasetImageCase
from chara import CaseCollection, BrainBoxCasePipeline
from brainbox.deciders.images.comfyui.workflows import Upscale
from brainbox import BrainBox
from foundation_kaia.marshalling import FileLike, File
from PIL import Image
from io import BytesIO


def _case_to_upscale_task(case: DatasetImageCase) -> BrainBox.Task:
    return Upscale(case.source.name)

def _case_to_upscale_upload(case: DatasetImageCase) -> FileLike:
    image = Image.open(case.source)
    if case.crop is not None:
        image = case.crop.crop(image)
    buf = BytesIO()
    image.save(buf, format='PNG')
    return File(case.source.name, buf.getvalue())

def upscale(cases: CaseCollection[DatasetImageCase]) -> CaseCollection[DatasetImageCase]:
    pipe = BrainBoxCasePipeline(
        _case_to_upscale_task,
        'upscaled_local_path',
        result_to_file=True,
        uploader=BrainBoxCasePipeline.Uploader(_case_to_upscale_upload)
    )
    return pipe(cases)