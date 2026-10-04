from chara.common import Chara
from brainbox.deciders import WhisperKenLM


class KenLMTrainingPipeline:
    def __call__(self, texts: list[str]) -> None:
        corpus = '\n'.join(t.strip().lower() for t in texts if t.strip())
        Chara.Apis.brainbox_api.execute(WhisperKenLM.new_task().train_lm(corpus))
