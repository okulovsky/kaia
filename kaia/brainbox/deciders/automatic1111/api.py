from typing import Optional
from .settings import Automatic1111Settings
from copy import copy
import requests
import base64
from ...core import File, IApiDecider
from ..arch.utils import FileLike
from enum import Enum
from uuid import uuid4

class Automatic1111(IApiDecider):
    class Interrogation(Enum):
        clip = 'clip'
        deepdanbooru = 'deepdanbooru'



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


    def interrogate(self, image: FileLike.Type, model: Optional['Automatic1111.Interrogation'] = None):
        if model is None:
            model = Automatic1111.Interrogation.deepdanbooru
        model = model.value
        with FileLike(image, self.file_cache) as file:
            data = file.read()
            b64 = base64.b64encode(data).decode('ascii')
            request_body = dict(image=b64, model=model)
            result = requests.post(f'http://{self.address}:{self.settings.port}/sdapi/v1/interrogate', json=request_body)
            if result.status_code != 200:
                raise ValueError(f"Automatic1111 returned status code {result.status_code}\n{result.text}")
            return result.json()


    def upscale(self, image: FileLike.Type, scale: float|int=2, model: str = 'ESRGAN_4x'):
        with FileLike(image, self.file_cache) as file:
            data = file.read()
            data = base64.b64encode(data).decode('ascii')
            payload = {
                "resize_mode": 0,
                "show_extras_results": True,
                "gfpgan_visibility": 0,
                "codeformer_visibility": 0,
                "codeformer_weight": 0,
                "upscaling_resize": scale,
                "upscaling_crop": True,
                "upscaler_1": model,
                "upscaler_2": "None",
                "extras_upscaler_2_visibility": 0,
                "upscale_first": False,
                "image": data
            }
            result = requests.post(
                f'http://{self.address}:{self.settings.port}/sdapi/v1/extra-single-image',
                json=payload
            )
            if result.status_code != 200:
                raise ValueError(f"Automatic1111 returned status code {result.status_code}\n{result.text}")
            result = base64.b64decode(result.json()['image'])
            return File(
                str(uuid4()) + '.png',
                result,
                File.Kind.Image
            )




