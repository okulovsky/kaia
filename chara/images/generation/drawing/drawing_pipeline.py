from chara import Chara
from chara.common import CaseCollection, BrainBoxCasePipeline
from .case import DrawingCase
from brainbox.deciders import Yolo
from .self_review import create_self_review_task
from chara.common.tools.llm import parse_json


def create_drawing_task(case: DrawingCase):
    case.workflow = case.scenario.to_workflow()
    return case.workflow

def create_face_detection_task(case: DrawingCase):
    return Yolo.new_task().analyze(case.image.name, Yolo.Models.yolov8_face)



class DrawingPipeline:
    def _set_self_review(self, case: DrawingCase, result):
        case.self_review = parse_json(result)

    def __call__(self, cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        pipeline = BrainBoxCasePipeline(
            create_drawing_task,
            'image',
            result_to_file=True
        )
        cases = Chara.call(pipeline, 'generation')(cases).successes_collection

        pipeline = BrainBoxCasePipeline(
            create_face_detection_task,
            'face_detection',
        )

        cases = Chara.call(pipeline, 'face_detection')(cases).successes_collection
        pipeline = BrainBoxCasePipeline(
            create_self_review_task,
            self._set_self_review
        )
        cases = Chara.call(pipeline, 'self_review')(cases).successes_collection

        return cases
