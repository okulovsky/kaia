from ....framework import DockerWebServiceApi
import requests
from .settings import LlamaLoraServerSettings
from .controller import LlamaLoraServerController
import typing as tp


class LlamaLoraServer(DockerWebServiceApi[LlamaLoraServerSettings, LlamaLoraServerController]):
    def __init__(self, tasknames, address: str | None = None):
        super().__init__(address)
        self.taskname2id = {taskname: id_ for id_, taskname in enumerate(tasknames)}

    def _check_endpoint_code(self, code: int, endpoint: str) -> None:
        if code != 200:
            if code == 503:
                raise RuntimeError(f"Model for {endpoint} is still loading")
            raise RuntimeError(f"Endpoint /{endpoint} returned unexpected status code {code}")

    def health(self) -> bool:
        response = requests.get(self.endpoint("/health"))
        try:
            self._check_endpoint_code(response.status_code, "health")
        except RuntimeError:
            return False
        return True

    def completion(
        self,
        *,
        task_name: str,
        prompt: tp.Optional[str] = None,
        prompts: tp.Optional[list[str]] = None,
        max_tokens: int = -1,
    ) -> str | list[str]:
        if prompt is None and prompts is None:
            raise ValueError("You must provide either `prompt` or `prompts`, none given.")
        if prompt is not None and prompts is not None:
            raise ValueError("You must provide either `prompt` or `prompts`, not both.")

        id_ = self.taskname2id[task_name]
        payload = {
            "prompt": prompt or prompts,
            "n_predict": max_tokens,
            "temperature": 0.0,  # TODO: might need to support later (e.g. for paraphrasing)
            "stream": False,  # TODO: might need to support later (e.g. for paraphrasing)
            "lora": [{"id": id_, "scale": 1.0}],
            "response_fields": ["content"],  # TODO: add "stop" for stream=True
        }
        response = requests.post(
            self.endpoint("/completion"),
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        self._check_endpoint_code(response.status_code, "completion")
        data = response.json()

        if prompt is not None:
            return data["content"]
        else:
            return [item["content"] for item in data]

    Settings = LlamaLoraServerSettings
    Controller = LlamaLoraServerController
