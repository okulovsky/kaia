from .templates import DOCKERFILE, DEPENDENCIES
import subprocess
from yo_fluq_ds import *
from pathlib import Path
from kaia.infra import Loc, deployment


image_name = 'coqui-tts-training'

def kill():
    deployment.Deployment.kill_by_ancestor_name(deployment.LocalExecutor(), image_name)


def build():
    kill()
    deps = ' '.join(DEPENDENCIES.split('\n'))
    docker = DOCKERFILE.format(dependencies=deps)
    FileIO.write_text(docker,Path(__file__).parent/'Dockerfile')
    subprocess.call(f'docker build -t {image_name} .', cwd=Path(__file__).parent)



def _run(*arguments):
    kill()
    run_arguments = [
        'docker','run','--name', image_name,
        '--mount', f'type=bind,source={Loc.data_folder/"audio_training"},target=/data',
        '--mount', f'type=bind,source={Loc.root_folder},target=/repo',
        '--gpus', 'all',
        '-p', f'8899:8899',
        image_name
    ] + list(arguments)
    subprocess.call(run_arguments)


def run_yourtts(dataset_zip, base_model_pth):
    _run('yourtts',dataset_zip, base_model_pth)


def run_vits(dataset_zip, base_model_pth):
    _run('vits',dataset_zip, base_model_pth)


def run_vits_multispeaker(dataset_zip, base_model_pth):
    _run('vits-multispeaker',dataset_zip, base_model_pth)


def run_notebook():
    _run('notebook')