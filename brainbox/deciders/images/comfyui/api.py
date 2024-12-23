import os
from ....framework import DockerWebServiceApi, File, FileLike, BrainBoxApi
from .workflows import IWorkflow
from .settings import ComfyUISettings
from .controller import ComfyUIController
import requests
import time
from pathlib import Path
from kaia.infra import FileIO


class ComfyUI(DockerWebServiceApi[ComfyUISettings, ComfyUIController]):
    def __init__(self, address: str = None):
        super().__init__(address)


    def run_on_dictionary(self, _tp, **kwargs):
        workflow = _tp(**kwargs)
        return self.run_workflow(workflow)

    def __call__(self, workflow: IWorkflow):
        self.run_workflow(workflow)


    def run_workflow(self, workflow: IWorkflow, **kwargs):
        for key, value in kwargs.items():
            setattr(workflow, key, value)

        input_files = []

        for file in workflow.get_input_files():
            input_file_name = self.controller.resource_folder('input') / FileLike.get_name(file)
            input_files.append(input_file_name)
            with FileLike(file, self.cache_folder) as content:
                FileIO.write_bytes(content.read(), input_file_name)

        json = workflow.create_workflow_json(self.current_job_id)

        address = f'http://{self.address}/prompt'
        result = requests.post(address, json=dict(prompt=json))
        if result.status_code!=200:
            raise ValueError(
                f"Decider ComfyUI could not schedule the workflow {type(workflow)}:\n\n{result.text}\n\n{json}\n\n{[f.name for f in input_files]}"
            )

        while True:
            queue_state = requests.get(address).json()
            remaining = queue_state.get('exec_info', {}).get('queue_remaining', None)
            if remaining is None:
                raise ValueError(f"Unexpected state reply {queue_state}")
            if remaining == 0:
                break
            time.sleep(0.1)

        resulting_files = []
        output_folder = self.controller.resource_folder('output')
        for file in sorted(os.listdir(output_folder)):
            if file.startswith(self.current_job_id):
                resulting_files.append(File.read(output_folder/file))
                os.unlink(output_folder/file)

        for input_file_name in input_files:
            os.unlink(input_file_name)

        return workflow.postprocess(resulting_files)


    @staticmethod
    def get_models(api: BrainBoxApi):
        return api.controller_api.list_resources(ComfyUI, 'models/')

    Controller = ComfyUIController
    Settings = ComfyUISettings











