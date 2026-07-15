import uuid
import requests
from interface import IOllama, OllamaOptions
from foundation_kaia.marshalling import FileLike, FileLikeHandler
import base64

OLLAMA_URL = 'http://127.0.0.1:11434'
SESSION_ID = str(uuid.uuid4())


class OllamaService(IOllama):
    def __init__(self, model: str):
        self.model = model

    @staticmethod
    def _apply_options(body: dict, options: OllamaOptions|None) -> None:
        if options is None:
            return
        ollama_options, format = options.to_options_and_format()
        if ollama_options is not None:
            body['options'] = ollama_options
        if format is not None:
            body['format'] = format

    def completions_json(self,
                          prompt: str,
                          options: OllamaOptions|None = None,
                          ) -> dict:
        body = dict(model=self.model, prompt=prompt, stream=False)
        self._apply_options(body, options)
        reply = requests.post(f'{OLLAMA_URL}/api/generate', json=body)
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def completions(self,
                     prompt: str,
                     options: OllamaOptions|None = None,
                     ) -> str:
        return self.completions_json(prompt, options)['response']

    def question_json(self,
                      prompt: str,
                      system_prompt: str|None = None,
                      options: OllamaOptions|None = None,
                      image: FileLike|None = None,
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
        self._apply_options(body, options)
        reply = requests.post(f'{OLLAMA_URL}/api/chat', json=body)
        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        return reply.json()

    def question(self,
                 prompt: str,
                 system_prompt: str|None = None,
                 options: OllamaOptions|None = None,
                 image: FileLike|None = None,
                 ) -> str:
        return self.question_json(prompt, system_prompt, options, image)['message']['content']
