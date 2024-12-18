from typing import *
from dataclasses import dataclass, field
from kaia.infra import Loc
from pathlib import Path
import shutil
import os
import subprocess

@dataclass
class OobaboogaModel:
    url: str


    @property
    def name(self):
        return self.url.split('/')[-1]



def _default_models():
    return (
        OobaboogaModel('https://huggingface.co/unsloth/gemma-2-it-GGUF/resolve/main/gemma-2-2b-it.q3_k_m.gguf'),
        OobaboogaModel('https://huggingface.co/TheBloke/openchat_3.5-GGUF/resolve/main/openchat_3.5.Q5_K_M.gguf'),
    )


@dataclass
class OobaboogaSettings:
    image_name: str = 'oobabooga'
    api_port: int = 11006
    gui_port: int = 11007
    streaming_port: int = 11008
    startup_time_in_seconds = 60

    mouted_locations: tuple[str,...] = (
        'cache',
        'characters',
        'loras',
        'logs',
        'models',
        'prompts',
        'softprompts',
        'training'
    )

    copy_back_locations: tuple[str,...] = (
        'characters',
        'prompts',
        'training'
    )

    @property
    def all_resourse_subfolders(self):
        return self.mouted_locations+('cloudflare',)

    models_to_download: tuple[OobaboogaModel,...] = field(default_factory=_default_models)

    default_request: dict = field(default_factory=lambda:DEFAULT_REQUEST)

    TRANSFORMERS_CACHE = "/home/app/text-generation-webui/cache/"

    HF_HOME = "/home/app/text-generation-webui/cache/"




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



