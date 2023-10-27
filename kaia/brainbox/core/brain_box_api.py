import json
import os
from typing import *
import requests
import jsonpickle
from .job import BrainBoxJob
from .task import BrainBoxTask
from pathlib import Path

class BrainBoxWebApi:
    def __init__(self, address, cache_folder):
        self.address = address
        self.cache_folder = cache_folder

    def add_task(self, task: BrainBoxTask):
        return self.add(task.decider, task.method, task.arguments, task.id, task.dependencies, task.back_track, task.batch)

    def add(self,
            decider: str,
            method: str,
            arguments: Any,
            id: Optional[str] = None,
            dependencies: Optional[Dict[str,str]] = None,
            back_track: Any = None,
            batch: Optional[str] = None
            ) -> str:
        url = self.address+f'/add/{decider}/{method}'
        response = requests.post(
            url,
            json=dict(
                id=id,
                arguments = json.loads(jsonpickle.dumps(arguments)),
                dependencies = dependencies,
                back_track = json.loads(jsonpickle.dumps(back_track)),
                batch = batch)
        )
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.json()

    def get_tasks(self, batch: Optional[str] = None) -> List[Dict]:
        addr = self.address+'/jobs'
        if batch is not None:
            addr += '/'+batch
        response = requests.get(addr)
        if response.status_code!=200:
            raise ValueError(response.text)
        return jsonpickle.loads(response.text)

    def get_task(self, id) -> BrainBoxJob:
        response = requests.get(self.address+'/job/'+id)
        try:
            data = jsonpickle.loads(response.text)
            return BrainBoxJob(**data)
        except:
            raise ValueError(response.text)

    def get_result(self, id) -> Any:
        response = requests.get(self.address+'/result/'+id)
        try:
            return jsonpickle.loads(response.text)
        except:
            raise ValueError(response.text)

    def get_file(self, fname):
        response = requests.get(self.address+"/file/"+fname)
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content

    def download(self, fname, custom_file_path: Optional[Path] = None, replace: bool = False):
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

    def cancel(self, id: str):
        requests.post(self.address+'/cancel/'+id)


    def cancel_all(self):
        tasks = self.get_tasks()
        for t in tasks:
            self.cancel(t['id'])





