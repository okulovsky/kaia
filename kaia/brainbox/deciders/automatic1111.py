from typing import *
import subprocess
from ...infra import Loc
from pathlib import Path
from ..core import IDecider
from IPython.display import HTML
import requests
from copy import deepcopy
from threading import Thread
import time
from PIL import Image
from io import BytesIO
import base64
from uuid import uuid4
from dataclasses import dataclass, field


@dataclass
class Automatic1111Settings:
    environment = 'automatic1111'
    automatic1111_path = Loc.root_folder.parent / 'stable-diffusion-webui'
    port = 7860
    max_boot_time_in_seconds: int = 20
    default_request: Dict = field(default_factory=lambda:DEFAULT_REQUEST)
    attempts_if_404: int = 10
    @property
    def python_path(self):
        return Loc.get_python_by_env(self.environment)

    @property
    def url(self):
        return f'http://127.0.0.1:{self.port}'



class Automatic1111(IDecider):
    def __init__(self, settings: Automatic1111Settings):
        self.settings = settings
        self.process = None #type: Optional[subprocess.Popen]

    def warmup(self, parameters: str):
        response = HTML(f'<a href={self.settings.url} target=_blank>Open Automatic1111 in browser</a>')
        try:
            requests.get(self.settings.url)
            return response
        except:
            pass

        arguments = [
                Loc.get_python_by_env(self.settings.environment),
                self.settings.automatic1111_path/'launch.py',
                '--api',
                '--nowebui',
                '--port',
                str(self.settings.port)
            ]
        if parameters is not None:
            arguments.extend(['--ckpt',parameters])

        self.process = subprocess.Popen(
            arguments,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=self.settings.automatic1111_path
        )
        for _ in range(self.settings.max_boot_time_in_seconds):
            time.sleep(1)
            try:
                requests.get(self.settings.url)
                return response
            except:
                pass
        raise ValueError("Seems like AUTO1 server has failed to boot up")


    def cooldown(self, parameters: str):
        if self.process is not None:
            self.process.terminate()


    def __call__(self, **kwargs):
        settings = deepcopy(self.settings.default_request)
        settings.update(**kwargs)

        reply = None
        for i in range(self.settings.attempts_if_404):
            reply = requests.post(self.settings.url + '/sdapi/v1/txt2img', json=settings)
            if reply.status_code == 200:
                break
            elif reply.status_code==404:
                time.sleep(1)
                continue
            else:
                raise ValueError(f"Automatic1111 returned an error code {reply.status_code}\n{reply.text}")
        if reply is None:
            raise ValueError(f"Automatic1111 was returning 404 for {self.settings.attempts_if_404} attempts")
        data = reply.json()
        if 'images' not in data:
            raise ValueError(f"Reply does not contain images\n{reply}")
        result = []
        for image in data['images']:
            image = Image.open(BytesIO(base64.decodebytes(bytes(image, "utf-8"))))
            fname = str(uuid4())+'.png'
            image.save(self.file_cache/fname)
            result.append(fname)
        return result

    def interrogate(self, image_b64, model):
        reply = requests.post(self.settings.url+'/sdapi/v1/interrogate', json=dict(image=image_b64,model=model))
        return reply.json()

DEFAULT_REQUEST = {
    'prompt': '',
    'styles': [],
    'negative_prompt': '',
    'seed': -1,
    'subseed': -1.0,
    'subseed_strength': 0,
    'seed_resize_from_h': 0,
    'seed_resize_from_w': 0,
    'sampler_name': 'DPM++ 2M Karras',
    'batch_size': 1,
    'n_iter': 1,
    'steps': 32,
    'cfg_scale': 11.5,
    'width': 512,
    'height': 512,
    'restore_faces': False,
    'tiling': False,
    'enable_hr': False,
    'denoising_strength': 0.61,
    'hr_scale': 2,
    'hr_upscaler': 'Latent',
    'hr_second_pass_steps': 0,
    'hr_resize_x': 0,
    'hr_resize_y': 0,
    'override_settings': {'CLIP_stop_at_last_layers': 2,
    'eta_noise_seed_delta': 31337,
    'always_discard_next_to_last_sigma': True}
}


