from chara.common import CharaApis
from brainbox.deciders import WhisperKenLM


class KenLMTrainingPipeline:
    def __call__(self, texts: list[str]) -> None:
        corpus  = '\n'.join(t.strip().lower() for t in texts if t.strip())
        task_id = CharaApis.brainbox_api.add(WhisperKenLM.new_task().train_lm(corpus))
        CharaApis.brainbox_api.join(task_id)
