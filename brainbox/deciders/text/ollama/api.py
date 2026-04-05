import uuid
import requests
from foundation_kaia.marshalling_2 import service
from foundation_kaia.brainbox_utils import brainbox_endpoint
from ....framework import DockerWebServiceApi, EntryPoint, TaskBuilder
from .model import OllamaModel
from .settings import OllamaSettings
from .controller import OllamaController

SESSION_ID = str(uuid.uuid4())


@service
class IOllama:
    @brainbox_endpoint
    def completions_json(self, prompt: str) -> dict:
        ...

    @brainbox_endpoint
    def completions(self, prompt: str) -> str:
        ...

    @brainbox_endpoint
    def question_json(self, prompt: str, system_prompt: str|None = None, options: dict|None = None, num_predict: int|None = None) -> dict:
        ...

    @brainbox_endpoint
    def question(self, prompt: str, system_prompt: str|None = None, options: dict|None = None, num_predict: int|None = None) -> str:
        ...


class OllamaApi(DockerWebServiceApi[OllamaSettings, OllamaController], IOllama):
    def __init__(self, address: str|None = None, parameter: str|None = None):
        super().__init__(address, parameter)

    def completions_json(self, prompt: str, **kwargs):
        reply = requests.post(
            f'http://{self.address}/api/generate',
            json=dict(
                model=self.container_parameter,
                prompt=prompt,
                stream=False,
                **kwargs,
            )
        )
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def completions(self, prompt: str, **kwargs):
        return self.completions_json(prompt, **kwargs)['response']

    def question_json(self, prompt: str, system_prompt: str|None = None, options: dict|None = None, num_predict: int|None = None):
        messages = []
        if system_prompt is not None:
            messages.append(dict(role='system', content=system_prompt))
        messages.append(dict(role='user', content=prompt))
        json = dict(
                model=self.container_parameter,
                messages=messages,
                stream=False,
                session_id=SESSION_ID
            )
        if options is not None:
            json['options'] = options
        if num_predict is not None:
            json['num_predict'] = num_predict
        reply = requests.post(f'http://{self.address}/api/chat', json=json)
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def question(self, prompt: str, system_prompt: str|None = None, options: dict|None = None, num_predict: int|None = None):
        return self.question_json(prompt, system_prompt, options, num_predict)['message']['content']


class OllamaTaskBuilder(TaskBuilder, IOllama):
    pass


class OllamaEntryPoint(EntryPoint[OllamaTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = OllamaApi
        self.Controller = OllamaController
        self.Settings = OllamaSettings
        self.Model = OllamaModel

Ollama = OllamaEntryPoint()
