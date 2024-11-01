import json
import os
import shutil
from unittest import TestCase
from ..arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner
from kaia.brainbox.deployment import IContainerRunner, SmallImageBuilder, IExecutor, Deployment
from .settings import OobaboogaSettings
from ...core import BrainBoxApi, BrainBoxTask, IntegrationTestResult, OneModelWarmuper, File
from .api import Oobabooga
from pathlib import Path
import requests
from kaia.infra import FileIO

class OobaboogaCopyBackRunner(IContainerRunner):
    def __init__(self, installer: 'OobaboogaInstaller'):
        self.installer = installer

    def run(self, image_name: str, container_name: str, executor: IExecutor):
        executor.execute([
            'docker', 'run', '--name', container_name,
            '--mount', self.arg_mount(self.installer.resource_folder('cache-back'), '/cache'),
            '--rm', '--entrypoint', '/bin/bash', image_name, '/home/app/copy_back.sh'
        ])



class OobaboogaInstaller(LocalImageInstaller):
    def __init__(self, settings:OobaboogaSettings):
        self.settings = settings
        super().__init__(
            'oobabooga',
            Path(__file__).parent/'container',
            DOCKERFILE,
            None,
            self._create_endpoint()
        )

    def _create_endpoint(self, model: str|None = None):
        mounts = {folder:'/home/app/text-generation-webui/'+folder for folder in self.settings.mouted_locations}
        mounts['cloudflare'] = '/etc/cloudflared'

        model_args = []
        if model is not None:
            model_args = ['--model', model]

        docker_run = BrainBoxServiceRunner(
            mount_resource_folders=mounts,
            publish_ports={
                self.settings.gui_port: 7860,
                self.settings.api_port: 5000
            },
            set_env_variables=dict(
                TRANSFORMERS_CACHE=self.settings.TRANSFORMERS_CACHE,
                HF_HOME=self.settings.HF_HOME
            ),
            command_line_arguments=['--listen','--api'] + model_args,
            mount_data_folder=False,
            gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
        )

        self.warmuper = OneModelWarmuper(
            OobaboogaInstaller.get_running_model,
            OobaboogaInstaller.run_with_given_model,
            OobaboogaInstaller._model_to_model_name
        )

        return DockerService(self, self.settings.gui_port, self.settings.startup_time_in_seconds, docker_run)

    @staticmethod
    def _model_to_model_name(model):
        return model['model_name']

    def create_api(self) -> Oobabooga:
        model = self.get_running_model()
        api = Oobabooga(self.ip_address, self.settings, model)
        return api

    def run_with_given_model(self, model: str):
        endpoint = self._create_endpoint(model)
        endpoint.kill()
        endpoint.run()
        endpoint.wait_for_running()

    def get_running_model(self):
        endpoint = self._create_endpoint(None)
        if not endpoint.is_running():
            return None
        model = requests.get(f'http://{self.ip_address}:{self.settings.api_port}/v1/internal/model/info').json()
        return model

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        for model in self.settings.models_to_download:
            yield IntegrationTestResult(0, "Model "+model.name)

            yield IntegrationTestResult(1, 'Completions')

            prompt = "Give me the recipe of the borsch."
            yield IntegrationTestResult(2, "Prompt", prompt)

            result = api.execute(BrainBoxTask.call(Oobabooga).completions_json(prompt=prompt).to_task(model.name))
            yield IntegrationTestResult(2, "Json", File("", json.dumps(result), File.Kind.Json))

            result = api.execute(BrainBoxTask.call(Oobabooga).completions(prompt=prompt).to_task(model.name))
            tc.assertIsInstance(result, str)
            yield IntegrationTestResult(2, "Text", result)

            yield IntegrationTestResult(1, 'Chat completions')

            prompt = "Give me the recipe of the borsch."
            yield IntegrationTestResult(2, "Prompt", prompt)

            result = api.execute(BrainBoxTask.call(Oobabooga).chat_completions_json(prompt=prompt).to_task(model.name))
            yield IntegrationTestResult(2, "Json", File("", json.dumps(result), File.Kind.Json))

            result = api.execute(BrainBoxTask.call(Oobabooga).chat_completions(prompt=prompt).to_task(model.name))
            tc.assertIsInstance(result, str)
            yield IntegrationTestResult(2, "Text", result)

    def pre_install(self):
        lines = []
        for name in self.settings.mouted_locations:
            lines.append(f'cp -R /home/app/text-generation-webui/{name} /cache/{name}/')
        with open(Path(__file__).parent/'container/copy_back.sh', 'wb') as file:
            file.write(chr(10).join(lines).encode('ascii'))


    def post_install(self):
        shutil.rmtree(self.resource_folder('cache-back'))
        deployment = Deployment(
            self._image_source,
            OobaboogaCopyBackRunner(self),
            self._executor
        )
        deployment.stop().remove().run()

        for folder in self.settings.copy_back_locations:
            #shutil.rmtree(self.resource_folder(folder))
            for file in os.listdir(self.resource_folder('cache-back', folder)):
                target_path = self.resource_folder(folder)/file
                if target_path.is_file() or target_path.is_dir():
                    continue
                src_path = self.resource_folder('cache-back', folder)/file

                if src_path.is_file():
                    #print(f"FILE {src_path} -> {target_path}")
                    shutil.copy(src_path, target_path)
                elif src_path.is_dir:
                    #print(f"FOLDER {src_path} -> {target_path}")
                    shutil.copytree(src_path, target_path)
                else:
                    raise ValueError("Error")


        for model in self.settings.models_to_download:
            fname = self.resource_folder('models')/model.url.split('/')[-1]
            if fname.is_file():
                continue
            self._executor.execute(['curl','-L',model.url,'--output',str(fname)])

    def warmup(self, parameters: str):
        self.warmuper.load_model(self, parameters)


    def create_brainbox_decider_api(self, parameters: str) -> Oobabooga:
        self.warmuper.check_and_return_running_model(self, parameters)
        return self.create_api()


    







DOCKERFILE = f'''
FROM ubuntu:22.04

WORKDIR /builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,rw \
    apt update && \
    apt install --no-install-recommends -y git vim build-essential python3-dev pip bash curl && \
    rm -rf /var/lib/apt/lists/*

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app/

RUN git clone https://github.com/oobabooga/text-generation-webui.git

WORKDIR /home/app/text-generation-webui

RUN GPU_CHOICE=A USE_CUDA118=FALSE LAUNCH_AFTER_INSTALL=FALSE INSTALL_EXTENSIONS=TRUE ./start_linux.sh --verbose

COPY copy_back.sh /home/app/

ENTRYPOINT ["/bin/bash", "/home/app/text-generation-webui/start_linux.sh"]
'''