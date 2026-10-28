from chara.common import Chara
from brainbox.deciders import WhisperKenLM


class KenLMTrainingPipeline:
    @staticmethod
    def corpus(texts: list[str]) -> str:
        return '\n'.join(t.strip().lower() for t in texts if t.strip())

    def __call__(self, texts: list[str]) -> None:
        Chara.Apis.brainbox_api.execute(WhisperKenLM.new_task().train_lm(self.corpus(texts)))
