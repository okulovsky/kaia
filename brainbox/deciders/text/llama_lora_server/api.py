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

    def health(self) -> tp.Any:
        response = requests.get(self.endpoint("/health"))
        self._check_endpoint_code(response.status_code, "health")
        return response.json()  # {"status":"ok"}

    def completion(self, task_name: str, prompt: str, max_tokens: int = -1) -> str:
        id_ = self.taskname2id[task_name]
        payload = {
            "prompt": prompt,
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
        if "content" not in data:
            raise ValueError("Expected content field in response")

        return data["content"]

    Settings = LlamaLoraServerSettings
    Controller = LlamaLoraServerController
