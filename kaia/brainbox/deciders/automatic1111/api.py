from .settings import Automatic1111Settings
from copy import copy
import requests
import base64
from ...core import File, IApiDecider


class Automatic1111(IApiDecider):
    def __init__(self, address: str, settings: Automatic1111Settings):
        self.address = address
        self.settings = settings

    def text_to_image(self, prompt: str, negative_prompt: str):
        request = copy(self.settings.default_request)
        request['prompt'] = prompt
        request['negative_prompt'] = negative_prompt
        response = requests.post(f'http://{self.address}:{self.settings.port}/sdapi/v1/txt2img', json=request)
        if response.status_code!=200:
            raise ValueError(f"Automatic1111 returned status code {response.status_code}\n{response.text}")
        js = response.json()
        result = []
        task_id = self.current_job_id
        for index, image in enumerate(js['images']):
            data = base64.b64decode(image)
            result.append(File(f'{task_id}.{index}.png', data, File.Kind.Image))
        return result

