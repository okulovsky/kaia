from typing import *
import os
import shutil
from abc import ABC, abstractmethod
from kaia.brainbox.core import IApiDecider, File
from ..arch.utils import FileLike
import requests
import time
from pathlib import Path
from yo_fluq_ds import Query
from kaia.infra import FileIO
from dataclasses import dataclass


class IWorkflow:
    @abstractmethod
    def create_workflow_json(self, job_id: str):
        pass


    @abstractmethod
    def get_input_files(self) -> list[FileLike.Type]:
        pass

    def postprocess(self, files: list[File]):
        return files



class ComfyUI(IApiDecider):
    def __init__(self,
                 address: str,
                 input_folder: Path,
                 output_folder: Path,
                 ):
        self.address = address
        self.input_folder = input_folder
        self.output_folder = output_folder


    def __call__(self, workflow: IWorkflow):
        return self.run_workflow(workflow)

    def run_workflow(self, workflow: IWorkflow, **kwargs):
        for key, value in kwargs.items():
            setattr(workflow, key, value)

        input_files = []

        for file in workflow.get_input_files():
            input_file_name = self.input_folder / FileLike.get_name(file)
            input_files.append(input_file_name)
            with FileLike(file, self.file_cache) as content:
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
        for file in sorted(os.listdir(self.output_folder)):
            if file.startswith(self.current_job_id):
                resulting_files.append(File.read(self.output_folder/file))
                os.unlink(self.output_folder/file)

        for input_file_name in input_files:
            os.unlink(input_file_name)

        return workflow.postprocess(resulting_files)














