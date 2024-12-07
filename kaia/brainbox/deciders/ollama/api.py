import requests
from ...core import IApiDecider

class Ollama(IApiDecider):
    def __init__(self, address: str, model: str = None):
        self.address = address
        self.model = model

    def with_model(self, model: str) -> 'Ollama':
        self.model = model
        return self


    def completions_json(self, prompt: str, **kwargs):
        reply = requests.post(
            f'http://{self.address}/api/generate',
            json=dict(
                model=self.model,
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
                model=self.model,
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

