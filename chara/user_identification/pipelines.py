import os.path

import numpy as np
from brainbox import BrainBox
from brainbox.deciders import Resemblyzer, InsightFace
from .helpers import UserSampleCase, collect_from_cache, collect_from_resources
from chara import Chara, BrainBoxCasePipeline, AnnotationPipeline, AudioLabelAnnotator, LabelAnnotatorSettings, \
    CaseCollection, SimpleTaskPlanner, ImageLabelAnnotator, logger
from .vector_annotation import VectorTaskPlanner
from typing import Any, Callable
from dataclasses import dataclass
from avatar.daemon import SpeakerIdentificationService, UserWalkInService
from datetime import datetime

@dataclass
class Identification:
    prefix: str
    suffix: str
    vector_task_factory: Callable[[UserSampleCase], BrainBox.Task]
    vector_applicator: Callable[[UserSampleCase, Any], None]
    service: type
    annotator_type: type


    def _create_annotator(self, users: tuple[str,...], task_planer, mock_annotation=None):
        settings = LabelAnnotatorSettings(users, "SKIP")
        annotator = self.annotator_type(lambda case: case.local_path, settings, task_planer, mock_annotation=mock_annotation)
        pipe = AnnotationPipeline(annotator, 'annotation')
        return pipe

    def _stash_current_dataset(self):
        src_folder = 'current/'
        files = Chara.Apis.avatar_api.resources(self.service).list(src_folder,glob=True)
        folder = 'before_'+str(datetime.now())
        for file in files:
            content = Chara.Apis.avatar_api.resources(self.service).read(os.path.join(src_folder, file))
            new_file = folder+'/'+file
            Chara.Apis.avatar_api.resources(self.service).upload(new_file, content)



    def _upload_new_dataset(self, users: tuple[str,...], cases: CaseCollection[UserSampleCase]):
        Chara.call(self._stash_current_dataset)()

        @Chara.phase
        def delete_current_dataset():
            if Chara.Apis.avatar_api.resources(self.service).is_dir('current'):
                Chara.Apis.avatar_api.resources(self.service).delete('current')

        @Chara.phase
        def upload_current_dataset():
            good_cases = [c for c in cases.successes if c.annotation in users]
            for case in good_cases:
                Chara.Apis.avatar_api.resources(self.service).upload(f'current/{case.annotation}/{case.file}', case.local_path)



    def annotation(self, users: tuple[str,...], mock_annotation=None) -> CaseCollection[UserSampleCase]:
        cases = Chara.call(collect_from_cache)(self.prefix, self.suffix)
        unit = BrainBoxCasePipeline(self.vector_task_factory, self.vector_applicator)
        cases = Chara.call(unit.__call__, 'computing_vectors')(cases).raise_if_all_errors()
        logger.info(f"{len(cases.cases)} total, {len(cases.successes)} to annotate")
        task_planner = VectorTaskPlanner(users)
        pipe = self._create_annotator(users, task_planner, mock_annotation)
        cases = Chara.call(pipe.__call__)(cases).raise_if_any_error()
        Chara.call(self._upload_new_dataset)(users, cases)
        return cases

    def refinement(self, mock_annotation=None) -> CaseCollection[UserSampleCase]:
        cases = Chara.call(collect_from_resources)(self.service)
        users = tuple(sorted(set(c.prior_annotation for c in cases.successes)))
        unit = BrainBoxCasePipeline(self.vector_task_factory, self.vector_applicator)
        cases = Chara.call(unit.__call__, "computing_vectors")(cases).raise_if_all_errors()
        pipe = self._create_annotator(users+('DELETE',), SimpleTaskPlanner(), mock_annotation)
        cases = Chara.call(pipe.__call__)(cases).raise_if_all_errors()
        Chara.call(self._upload_new_dataset)(users, cases)
        return cases





class VoiceIdentification(Identification):
    def _merge(self, case: UserSampleCase, result: Any) -> None:
        case.vector = np.array(result)

    def _create_task(self, case: UserSampleCase) -> BrainBox.Task:
        return Resemblyzer.new_task().vector(case.file)

    def __init__(self):
        super().__init__(
            'recording',
            '.wav',
            self._create_task,
            self._merge,
            SpeakerIdentificationService,
            AudioLabelAnnotator
        )

class FaceIdentification(Identification):
    def _create_task(self, case: UserSampleCase) -> BrainBox.Task:
        return InsightFace.new_task().analyze(case.file)

    def _merge(self, case: UserSampleCase, result: Any) -> None:
        if len(result) == 0:
            case.error = 'No faces detected'
        elif len(result) > 1:
            case.error = 'Many faces detected'
        else:
            case.vector = np.array(result[0]['embedding'])


    def __init__(self):
        super().__init__(
            'webcam',
            '.jpg',
            self._create_task,
            self._merge,
            UserWalkInService,
            ImageLabelAnnotator
        )
