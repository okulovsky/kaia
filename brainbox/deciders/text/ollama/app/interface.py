from foundation_kaia.marshalling import service, FileLike
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IOllama:
    @brainbox_endpoint
    def completions_json(self, prompt: str) -> dict:
        ...

    @brainbox_endpoint
    def completions(self, prompt: str) -> str:
        ...

    @brainbox_endpoint
    def question_json(self,
                      prompt: str,
                      system_prompt: str|None = None,
                      options: dict|None = None,
                      num_predict: int|None = None,
                      image: FileLike|None = None,
                      ) -> dict:
        ...

    @brainbox_endpoint
    def question(self,
                 prompt: str,
                 system_prompt: str|None = None,
                 options: dict|None = None,
                 num_predict: int|None = None,
                 image: FileLike|None = None,
                 ) -> str:
        ...
