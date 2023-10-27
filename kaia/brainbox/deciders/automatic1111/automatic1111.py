from typing import *
import subprocess
from ....infra import Loc
from pathlib import Path
from ...core import IDecider
from IPython.display import HTML
import requests
from copy import deepcopy
from threading import Thread
import time
from PIL import Image
from io import BytesIO
import base64
from uuid import uuid4


class Automatic1111Request:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.reply = None

    def run(self):
        reply = requests.post(self.url, json=self.payload)
        self.reply = reply.json()


class Automatic1111(IDecider):
    def __init__(self,
                 location: Path,
                 environment_name: str,
                 port: int,
                 boot_time_in_seconds: int = 20,
                 request_timeout_in_seconds: int = 1000,
                 ):
        self.location = location
        self.environment_name = environment_name
        self.url = f'http://127.0.0.1:{port}'
        self.boot_time_in_seconds = boot_time_in_seconds
        self.process = None #type: Optional[subprocess.Popen]
        self.default_settings = DEFAULT_SETTINGS
        self.request_timeout_in_seconds = request_timeout_in_seconds



    def warmup(self):
        response = HTML(f'<a href={self.url} target=_blank>Open Automatic1111 in browser</a>')
        try:
            requests.get(self.url)
            return response
        except:
            pass

        self.process = subprocess.Popen(
            [
                Loc.get_python_by_env(self.environment_name),
                self.location/'launch.py',
                '--api'
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=self.location
        )
        for _ in range(self.boot_time_in_seconds):
            time.sleep(1)
            try:
                requests.get(self.url)
                return response
            except:
                pass
        raise ValueError("Seems like AUTO1 server has failed to boot up")


    def cooldown(self):
        if self.process is not None:
            self.process.terminate()

    def _process_reply(self, reply):
        result = []
        for image in reply['images']:
            image = Image.open(BytesIO(base64.decodebytes(bytes(image, "utf-8"))))
            fname = str(uuid4())+'.png'
            image.save(self.file_cache/fname)
            result.append(fname)
        return result


    def generate(self,
                 **kwargs
                 ):
        settings = deepcopy(self.default_settings)
        settings.update(**kwargs)

        request = Automatic1111Request(self.url+'/sdapi/v1/txt2img', settings)
        thread = Thread(target = request.run)
        thread.start()

        for i in range(self.request_timeout_in_seconds):
            if request.reply is not None:
                return self._process_reply(request.reply)
            res = requests.get(self.url+'/sdapi/v1/progress')
            try:
                js = res.json()
                prog = js['progress']
                if isinstance(prog, float) or isinstance(prog, int):
                    self.progress_reporter.report_progress(prog)
            except:
                pass
            time.sleep(1)
        return None

    def interrogate(self, image_b64, model):
        request = Automatic1111Request(self.url+'/sdapi/v1/interrogate', payload=dict(image=image_b64,model=model))
        request.run()
        return request.reply




DEFAULT_SETTINGS = {
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


