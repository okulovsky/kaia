from chara import Chara, BrainBoxCasePipeline, CaseCollection
from brainbox.deciders import Piper
from .training_and_export import CheckpointCase
from yo_fluq import Query


def _case_to_upload_to_piper(case: CheckpointCase):
    return Piper.new_task().upload_tar_voice(case.checkpoint.filename, case.checkpoint.filename)

def _case_to_voiceover(case: CheckpointCase):
    return Piper.new_task().voiceover(case.text_to_voiceover, case.checkpoint.filename)

def _case_to_delete_from_piper(case: CheckpointCase):
    return Piper.new_task().delete_voice(case.checkpoint.filename)


def evaluate(cases: CaseCollection[CheckpointCase]) -> CaseCollection[CheckpointCase]:
    cases_with_different_models = CaseCollection(Query.en(cases.successes).distinct(lambda z: z.checkpoint.filename))

    @Chara.phase
    def uploading_models_to_cache():
        for case in cases_with_different_models.successes:
            if not Chara.Apis.brainbox_api.cache.is_file(case.checkpoint.filename):
                Chara.Apis.brainbox_api.cache.upload(case.checkpoint.filename, case.checkpoint.filename)

    pipe = BrainBoxCasePipeline(_case_to_upload_to_piper, None)
    Chara.call(pipe)(cases_with_different_models)

    pipe = BrainBoxCasePipeline(_case_to_voiceover, 'path_to_voiceover_file', result_to_file=True)
    cases = Chara.call(pipe.__call__)(cases)

    pipe = BrainBoxCasePipeline(_case_to_delete_from_piper, None)
    Chara.call(pipe.__call__)(cases)

    @Chara.phase
    def removing_models_from_cache():
        for case in cases_with_different_models.successes:
            if Chara.Apis.brainbox_api.cache.is_file(case.checkpoint.filename):
                Chara.Apis.brainbox_api.cache.delete(case.checkpoint.filename)

    return cases