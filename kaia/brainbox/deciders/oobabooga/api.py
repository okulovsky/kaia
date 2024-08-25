import requests
from .settings import OobaboogaSettings
from ...core import IApiDecider
from copy import copy

class Oobabooga(IApiDecider):
    def __init__(self, ip_address: str, settings: OobaboogaSettings, model: dict):
        self.settings = settings
        self.model = model
        self.address = f'{ip_address}:{settings.api_port}'


    def completions_json(self, prompt, **kwargs):
        request = copy(self.settings.default_request)
        for key, value in kwargs.items():
            request[key] = value
        request['prompt'] = prompt

        response = requests.post(f'http://{self.address}/v1/completions', json=request)
        if response.status_code != 200:
            raise ValueError(f'Status code {response.status_code}, value\n{response.text}')
        return response.json()

    def completions(self, prompt, **kwargs):
        return self.completions_json(prompt, **kwargs)['choices'][0]['text']

    def chat_completions_json(self, prompt):
        response = requests.post(f'http://{self.address}/v1/chat/completions', json={
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "mode": "instruct",
            "instruction_template": "Alpaca"
        })
        if response.status_code != 200:
            raise ValueError(f'Status code {response.status_code}, value\n{response.text}')
        return response.json()

    def chat_completions(self, prompt):
        response = self.chat_completions_json(prompt)
        assistant_message = response['choices'][0]['message']['content']
        return assistant_message
