import threading
import time
from typing import Iterable
from unittest import TestCase
import json

import requests

from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from kaia.brainbox.deployment import SmallImageBuilder
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, OneOrNoneModelWarmuper, File
from .settings import Automatic1111Settings
from .api import Automatic1111
from pathlib import Path
import copy

class Automatic1111Installer(LocalImageInstaller):
    def __init__(self, settings:Automatic1111Settings):
        self.settings = settings

        super().__init__(
            'automatic1111',
            Path(__file__).parent/'container',
            DOCKERFILE,
            None,
            self._create_endpoint(None)
        )

        self.warmuper = OneOrNoneModelWarmuper(
            Automatic1111Installer._get_status,
            Automatic1111Installer.run_with_given_model,
        )

    def _create_endpoint(self, model_name):
        model_arg = []
        if model_name is not None:
            model_arg = ['--ckpt', '/home/app/stable-diffusion-webui/models/Stable-diffusion/'+model_name]

        runner = BrainBoxServiceRunner(
            mount_resource_folders={
                'models': '/home/app/stable-diffusion-webui/models/',
                'embeddings': '/home/app/stable-diffusion-webui/embeddings'
            },
            gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
            vram_in_gb_required=5,
            publish_ports={self.settings.port: 7860},
            command_line_arguments=[ "--listen", "--api"] + model_arg
        )
        return DockerService(self, self.settings.port, 20, runner)

    def _get_status(self):
        if not self.main_service.is_running():
            return OneOrNoneModelWarmuper.Status(False, None)

        for i in range(10):
            opt = requests.get(f'http://{self.ip_address}:{self.settings.port}/sdapi/v1/options').json()
            if 'sd_model_checkpoint' in opt and opt['sd_model_checkpoint'] is not None:
                checkpoint = opt['sd_model_checkpoint'].split(' ')[0]
                return OneOrNoneModelWarmuper.Status(True, checkpoint)
            time.sleep(1)



    def run_with_given_model(self, model: str):
        endpoint = self._create_endpoint(model)
        endpoint.kill()
        endpoint.run()
        endpoint.wait_for_running()


    def post_install(self):
        endpoint = copy.deepcopy(self.main_service._container_runner)
        endpoint._detach = False
        endpoint._interactive = False
        endpoint = DockerService(self, None, None, endpoint)
        thread = threading.Thread(target=endpoint.run, daemon=True)
        thread.start()
        while not self.is_running():
            time.sleep(0.1)
        api = self.create_api()
        api.text_to_image('Cute little kitten','')
        self.kill()
        thread.join()

        for model in self.settings.sd_models_to_download:
            fname = self.resource_folder('models')/'Stable-diffusion'/model.filename
            if fname.is_file():
                continue
            self._executor.execute(['curl','-L',model.url,'--output',str(fname)])

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable[IntegrationTestResult]:
        yield  IntegrationTestResult(0, "Generation")
        prompt = "masterpiece, best quality, city, japan, sunny day, ocean, mountain"
        yield IntegrationTestResult(1, "Prompt", prompt)
        negative_prompt = "bad quality, dull colors, monochrome"
        yield IntegrationTestResult(1, "Negative prompt", negative_prompt)
        for model in self.settings.sd_models_to_download:
            yield IntegrationTestResult(2, f"Model {model.filename}")
            task = BrainBoxTask.call(Automatic1111).text_to_image(
                prompt=prompt,
                negative_prompt=negative_prompt
            ).to_task(decider_parameters = model.filename)
            results = api.execute(task)
            for result in results:
                api.pull_content(result)
                yield IntegrationTestResult(2, None, result)

        yield IntegrationTestResult(0, "Image processing")
        image = File.read(Path(__file__).parent/'image.png')
        yield IntegrationTestResult(1, "Input image", image)

        api.upload(image.name, image.content)

        interrogation = api.execute(BrainBoxTask.call(Automatic1111).interrogate(image=image.name))
        js = File("response.json", json.dumps(interrogation), File.Kind.Json)
        yield IntegrationTestResult(2, "Interrogation", js)

        upscale = api.execute(BrainBoxTask.call(Automatic1111).upscale(image=image.name))
        api.pull_content(upscale)
        yield IntegrationTestResult(2, "Upscaling", upscale)




    def create_api(self):
        return Automatic1111(self.ip_address, self.settings)

    def warmup(self, parameters: str):
        self.warmuper.load_model(self, parameters)

    def create_brainbox_decider_api(self, parameters: str) -> Automatic1111:
        self.warmuper.check_and_return_running_model(self, parameters)
        return self.create_api()


DOCKERFILE = f'''
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
	libgl1 libglib2.0-0 \
	python3 python3-venv \
	git \
	wget \
	vim \
	inetutils-ping \
	sudo \
	net-tools \
	iproute2 \
	&& \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*
	
{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

COPY webui.sh /home/app/webui.sh

RUN sed -i 's/\r$//' /home/app/webui.sh

USER root

RUN chmod +x /home/app/webui.sh

USER app

RUN echo 'venv_dir=/home/app/venv' > /home/app/webui-user.sh

ENV install_dir=/home/app

RUN /home/app/webui.sh --exit --skip-torch-cuda-test

ENV VIRTUAL_ENV=/home/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR "/home/app/stable-diffusion-webui/"

ENTRYPOINT ["python3", "launch.py"]
'''