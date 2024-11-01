from dataclasses import dataclass
import os
import time
from typing import *
import requests
from ..small_classes import BrainBoxJob, BrainBoxTask, BrainBoxTaskPack, IDecider, BrainBoxBase, LogItem, File
from ..small_classes.task_builder import BrainBoxTaskBuilder, BrainBoxTaskBuilderResult
from ..planers import SimplePlanner, AlwaysOnPlanner
from .web_server import BrainBoxEndpoints, BrainBoxWebServer
from .service import BrainBoxService
from pathlib import Path
from kaia.infra import MarshallingEndpoint, Loc, Sql
from kaia.infra.app import KaiaApp, SubprocessRunner
import uuid
from sqlalchemy.orm import Session
from threading import Thread
from sqlalchemy import select
from io import BytesIO
from .execute_serverless import execute_serverless

class BrainBoxApi(MarshallingEndpoint.API):
    def __init__(self, address: str, cache_folder: Path = Loc.temp_folder / 'brainbox_cache'):
        super().__init__(address)
        self.cache_folder = cache_folder

    def add(self, task: Union[BrainBoxTaskPack, BrainBoxTask, Iterable[BrainBoxTask]]):
        return_id = None
        if isinstance(task, BrainBoxTask) or isinstance(task, BrainBoxTaskBuilderResult):
            return_id = task.id
            task = [task]
        elif isinstance(task, BrainBoxTaskPack):
            if task.uploads is not None:
                for key, data in task.uploads.items():
                    self.upload(key, data)
            return_id = task.resulting_task.id
            task = list(task.intermediate_tasks) + [task.resulting_task]

        final_task = []
        for t in task:
            if isinstance(t, BrainBoxTaskBuilderResult):
                final_task.append(t.to_task())
            elif isinstance(t, BrainBoxTask):
                final_task.append(t)
            else:
                raise ValueError("Only BrainBoxTask is allowed in the list, if the argument is list")


        self.caller.call(BrainBoxEndpoints.add, list(final_task))
        return return_id

    def execute(self, task: Union[BrainBoxTaskPack, BrainBoxTask, Iterable[BrainBoxTask]]) -> Any:
        self.add(task)
        return self.join(task)

    def join(self, task: Union[BrainBoxTaskPack, str, BrainBoxTask, Iterable[str], Iterable[BrainBoxTask]]):
        if isinstance(task, str):
            input = [task]
        elif isinstance(task, BrainBoxTask) or isinstance(task, BrainBoxTaskBuilderResult):
            input = [task.id]
        elif isinstance(task, BrainBoxTaskPack):
            input = [task.resulting_task.id]
        else:
            input = [element.id if isinstance(element, BrainBoxTask)  or isinstance(element, BrainBoxTaskBuilderResult) else element for element in task]
        output = self.caller.call(BrainBoxEndpoints.join, input)
        if isinstance(task, str) or isinstance(task, BrainBoxTask) or isinstance(task, BrainBoxTaskBuilderResult):
            return output[0]
        elif isinstance(task, BrainBoxTaskPack):
            return task.postprocessor.postprocess(output[0], self)
        else:
            return output

    def get_summary(self, batch: Optional[str] = None) -> List[Dict]:
        return self.caller.call(BrainBoxEndpoints.summary, batch)

    def get_job(self, id) -> BrainBoxJob:
        return self.caller.call(BrainBoxEndpoints.job, id)

    def get_result(self, id) -> Any:
        return self.caller.call(BrainBoxEndpoints.result, id)

    def get_file(self, fname: str|File):
        if isinstance(fname, File):
            fname = fname.name
        response = requests.get(f'http://{self.caller.address}/file/{fname}')
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content

    def pull_content(self, file: File) -> File:
        file.content = self.get_file(file)
        return file

    def download(self, fname: str|File, custom_file_path: Optional[Path] = None, replace: bool = False) -> Path:
        if isinstance(fname, File):
            fname = fname.name
        if custom_file_path is None:
            custom_file_path = self.cache_folder/fname
        os.makedirs(custom_file_path.parent, exist_ok=True)
        if custom_file_path.is_file():
            if not replace:
                return custom_file_path
        data = self.get_file(fname)
        with open(custom_file_path, 'wb') as file:
            file.write(data)
            file.flush()
        return custom_file_path

    def upload(self, filename: str, data: Union[bytes|Path]):
        if isinstance(data, Path):
            stream = open(data,'rb')
        elif isinstance(data, bytes):
            stream = BytesIO(data)
        else:
            raise ValueError(f'Data must be Path or bytes, but was {type(data)}')
        reply = requests.post(
            f'http://{self.address}/upload',
            files=(
                (filename, stream),
            )
        )
        if reply.status_code != 200:
            raise ValueError(reply.text)



    class Test(MarshallingEndpoint.TestAPI):
        def __init__(self,
                     services,
                     cache_folder = None,
                     address = '127.0.0.1:8099',
                     always_on_planner: bool = False
                     ):
            if cache_folder is None:
                cache_folder = Loc.temp_folder / 'tests/brainboxwebservicetextfilecache'
            self.cache_folder = cache_folder
            self.address = address
            self.services = services
            self.always_on_planner = always_on_planner

        def __enter__(self) -> 'BrainBoxApi':
            service = BrainBoxService(
                self.services,
                AlwaysOnPlanner(False) if self.always_on_planner else SimplePlanner(5),
                self.cache_folder,
            )
            server = BrainBoxWebServer(8099, Sql.test_file('brainbox_web_test_db_' + str(uuid.uuid4())), self.cache_folder, service)
            api = BrainBoxApi(self.address, self.cache_folder)
            return self._prepare_service(api, server)

        execute_serverless = execute_serverless



BrainBoxTestApi = BrainBoxApi.Test
