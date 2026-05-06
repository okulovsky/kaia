from chara import Chara, BrainBoxCasePipeline, CaseCollection, logger
from brainbox.deciders import Piper
from .training_and_export import CheckpointCase
from yo_fluq import Query


def _case_to_upload_to_piper(case: CheckpointCase):
    return Piper.new_task().upload_tar_voice(case.checkpoint.filename+'.tar', case.checkpoint.filename+".tar")

def _case_to_voiceover(case: CheckpointCase):
    return Piper.new_task().voiceover(case.text_to_voiceover, case.checkpoint.filename+".tar")

def _case_to_delete_from_piper(case: CheckpointCase):
    return Piper.new_task().delete_voice(case.checkpoint.filename+".tar")


def evaluate(cases: CaseCollection[CheckpointCase]) -> CaseCollection[CheckpointCase]:
    cases_with_different_models = CaseCollection(Query.en(cases.successes).distinct(lambda z: z.checkpoint.filename).to_list())

    @Chara.phase
    def uploading_models_to_cache():
        for case in cases_with_different_models.successes:
            logger.info(f"Considering {case.checkpoint.filename}, located at {case.local_path}")
            if True:
                logger.info(f"Uploading {case.local_path}")
                Chara.Apis.brainbox_api.cache.upload(case.checkpoint.filename+".tar", case.local_path)

    pipe = BrainBoxCasePipeline(_case_to_upload_to_piper, None)
    Chara.call(pipe.__call__, "UploadingToPiper")(cases_with_different_models).raise_if_any_error()

    pipe = BrainBoxCasePipeline(_case_to_voiceover, 'path_to_voiceover_file', result_to_file=True)
    cases = Chara.call(pipe.__call__, "Voiceover")(cases)

    pipe = BrainBoxCasePipeline(_case_to_delete_from_piper, None)
    Chara.call(pipe.__call__, "DeleteFromPiper")(cases)

    @Chara.phase
    def removing_models_from_cache():
        for case in cases_with_different_models.successes:
            if Chara.Apis.brainbox_api.cache.is_file(case.checkpoint.filename):
                Chara.Apis.brainbox_api.cache.delete(case.checkpoint.filename)

    return cases