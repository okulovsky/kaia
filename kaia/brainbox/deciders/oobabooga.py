from typing import *
import subprocess
from pathlib import Path
from ..core import IDecider
from IPython.display import HTML
import requests
import time
from copy import copy
from dataclasses import dataclass, field
from kaia.infra import Loc

@dataclass
class OobaboogaSettings:
    environment = 'oobabooga'
    oobabooga_path = Loc.root_folder.parent/'text-generation-webui'
    exec_path = Loc.root_folder.parent/'text-generation-webui'/('start_windows.bat' if Loc.is_windows else 'start_linux.sh')
    port = 7860
    api_port = 5000
    default_model_name = '4bit_WizardLM-13B-Uncensored-4bit-128g'
    max_boot_time_in_seconds: int = 20
    request_timeout_in_seconds: int = 1000
    default_request: Dict = field(default_factory=lambda:DEFAULT_REQUEST)

    @property
    def url(self):
        return f'http://127.0.0.1:{self.api_port}'

    @property
    def gradio_url(self):
        return f'http://127.0.0.1:{self.port}'


class Oobabooga(IDecider):
    def __init__(self, settings: OobaboogaSettings):
        self.settings = settings
        self.process = None #type: Optional[subprocess.Popen]


    def warmup(self, parameters: str):
        model = parameters
        if model is None:
            model = self.settings.default_model_name

        response = HTML(f'<a href={self.settings.gradio_url} target=_blank>Open Oobabooga in browser</a>')
        try:
            reply = requests.get(self.settings.url)
            print(reply.text)
            return response
        except:
            pass

        self.process = subprocess.Popen(
            [
                self.settings.exec_path,
                '--listen',
                '--api',
                '--extensions',
                'openai',
                '--model',
                model
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=self.settings.oobabooga_path
        )

        ok = False
        for _ in range(self.settings.max_boot_time_in_seconds):
            time.sleep(1)
            try:
                requests.get(self.settings.url)
                ok = True
                break
            except:
                pass

        if not ok:
            raise ValueError("Seems like Oobabooga server has failed to boot up")

        requested_model = parameters if parameters is not None else self.settings.default_model_name

        reply = requests.post(self.settings.url+'/api/v1/model', json={'action': 'load', 'model_name': requested_model })
        if reply.status_code != 200:
            raise ValueError(f"load model request returned {reply.status_code}\n{reply.text}")

        model_name = reply.json().get('result', {}).get('model_name', '')
        if model_name!=requested_model:
            raise ValueError(f'load model returned `{model_name}`, but `{requested_model}` was expected\n{reply.json()}')

        return response


    def run(self, prompt, **kwargs):
        request = copy(self.settings.default_request)
        for key, value in kwargs.items():
            request[key] = value
        request['prompt'] = prompt

        response = requests.post(self.settings.url+'/api/v1/generate', json=request)
        if response.status_code != 200:
            raise ValueError(f'Status code {response.status_code}, value\n{response.text}')
        return response.json()['results'][0]['text']


    def cooldown(self, parameters: str):
        if self.process is not None:
            self.process.terminate()


DEFAULT_REQUEST = {
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