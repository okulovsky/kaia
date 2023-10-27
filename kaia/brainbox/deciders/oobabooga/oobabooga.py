from typing import *
import subprocess
from pathlib import Path
from ...core import IDecider
from IPython.display import HTML
import requests
import time
from copy import copy


class Oobabooga(IDecider):
    def __init__(self,
                 ooga_path: Path,
                 exec_path: Path,
                 port: int,
                 api_port: int,
                 model_name: str,
                 boot_time_in_seconds: int = 20,
                 request_timeout_in_seconds: int = 1000,
                 ):
        self.ooga_path = ooga_path
        self.exec_path = exec_path
        self.model_name = model_name
        self.url = f'http://127.0.0.1:{api_port}'
        self.gradio_url = f'http://127.0.0.1:{port}'
        self.boot_time_in_seconds = boot_time_in_seconds
        self.process = None #type: Optional[subprocess.Popen]
        self.default_settings = DEFAULT_SETTINGS
        self.request_timeout_in_seconds = request_timeout_in_seconds



    def warmup(self):
        response = HTML(f'<a href={self.gradio_url} target=_blank>Open Oobabooga in browser</a>')
        try:
            reply = requests.get(self.url)
            print(reply.text)
            return response
        except:
            pass

        self.process = subprocess.Popen(
            [
                self.exec_path,
                '--api'
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=self.ooga_path
        )

        ok = False
        for _ in range(self.boot_time_in_seconds):
            time.sleep(1)
            try:
                requests.get(self.url)
                ok = True
                break
            except:
                pass

        if not ok:
            raise ValueError("Seems like Oobabooga server has failed to boot up")

        reply = requests.post(self.url+'/api/v1/model', json={'action': 'load', 'model_name': self.model_name })
        if reply.status_code != 200:
            raise ValueError(f"load model request returned {reply.status_code}\n{reply.text}")

        model_name = reply.json().get('result', {}).get('model_name', '')
        if model_name!=self.model_name:
            raise ValueError(f'load model returned `{model_name}`, but `{self.model_name}` was expected\n{reply.json()}')

        return response


    def run(self, prompt, **kwargs):
        request = copy(self.default_settings)
        for key, value in kwargs.items():
            request[key] = value
        request['prompt'] = prompt

        response = requests.post(self.url+'/api/v1/generate', json=request)
        if response.status_code != 200:
            raise ValueError(f'Status code {response.status_code}, value\n{response.text}')
        return response.json()['results'][0]['text']


    def cooldown(self):
        if self.process is not None:
            self.process.terminate()


DEFAULT_SETTINGS = {
        'prompt': None,
        'max_new_tokens': 250,
        'auto_max_new_tokens': False,
        'max_tokens_second': 0,

        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'repetition_penalty_range': 0,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'grammar_string': '',
        'guidance_scale': 1,
        'negative_prompt': '',

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'custom_token_bans': '',
        'skip_special_tokens': True,
        'stopping_strings': []
    }