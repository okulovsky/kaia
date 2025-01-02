import requests
from ....framework import DockerWebServiceApi
from .model import OllamaModel
from .settings import OllamaSettings
from .controller import OllamaController

class Ollama(DockerWebServiceApi[OllamaSettings, OllamaController]):
    def __init__(self, address: str|None = None, parameter: str|None = None):
        super().__init__(address, parameter)


    def completions_json(self, prompt: str, **kwargs):
        reply = requests.post(
            f'http://{self.address}/api/generate',
            json=dict(
                model=self.container_parameter,
                prompt=prompt,
                stream=False,
                **kwargs
            )
        )
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def completions(self, prompt: str, **kwargs):
        return self.completions_json(prompt, **kwargs)['response']

    def question_json(self, prompt: str):
        reply = requests.post(
            f'http://{self.address}/api/chat',
            json=dict(
                model=self.container_parameter,
                messages=[
                    dict(role='user', content=prompt),
                ],
                stream=False
            )
        )
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def question(self, prompt: str):
        return self.question_json(prompt)['message']['content']


    Controller = OllamaController
    Settings = OllamaSettings
    Model = OllamaModel