import uuid
import requests
from interface import IOllama
from foundation_kaia.marshalling import FileLike, FileLikeHandler
import base64

OLLAMA_URL = 'http://127.0.0.1:11434'
SESSION_ID = str(uuid.uuid4())


class OllamaService(IOllama):
    def __init__(self, model: str):
        self.model = model

    def completions_json(self, prompt: str) -> dict:
        reply = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json=dict(model=self.model, prompt=prompt, stream=False),
        )
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def completions(self, prompt: str) -> str:
        return self.completions_json(prompt)['response']

    def question_json(self,
                      prompt: str,
                      system_prompt: str|None = None,
                      options: dict|None = None,
                      num_predict: int|None = None,
                      image: FileLike|None = None
                      ) -> dict:
        messages = []
        if system_prompt is not None:
            messages.append(dict(role='system', content=system_prompt))
        message = dict(role='user', content=prompt)
        if image is not None:
            bts = FileLikeHandler.to_bytes(image)
            message['images'] = [base64.b64encode(bts).decode()]
        messages.append(message)
        body = dict(model=self.model, messages=messages, stream=False, session_id=SESSION_ID)
        if options is not None:
            body['options'] = options
        if num_predict is not None:
            body['num_predict'] = num_predict
        reply = requests.post(f'{OLLAMA_URL}/api/chat', json=body)
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def question(self,
                 prompt: str,
                 system_prompt: str|None = None,
                 options: dict|None = None,
                 num_predict: int|None = None,
                 image: FileLike|None = None
                 ) -> str:
        return self.question_json(prompt, system_prompt, options, num_predict, image)['message']['content']
