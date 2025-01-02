from ....framework import DockerWebServiceApi, File, FileLike, CacheUploadPrerequisite
import requests
from .settings import BoilerplateSettings
from .controller import BoilerplateController
from .model import BoilerplateModel
import json


class Boilerplate(DockerWebServiceApi[BoilerplateSettings, BoilerplateController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def json(self, argument: str):
        result = requests.post(
            self.endpoint('/decide'),
            json = dict(
                argument=argument,
            )
        )
        if result.status_code!=200:
            raise ValueError(f"Endpoint /decide returned unexpected status code {result.status_code}\n{result.text}")
        return result.json()

    def file(self, argument: str):
        json_data = self.json(argument)
        return File(self.current_job_id+'.output.json', json.dumps(json_data), File.Kind.Json)

    def file_length(self, file_like: FileLike.Type):
        with FileLike(file_like, self.cache_folder) as stream:
            return len(stream.read())

    def resources(self):
        result = requests.get(self.endpoint('/resources'))
        if result.status_code!=200:
            raise ValueError(f"Endpoint /resources returned unexpected status code {result.status_code}\n{result.text}")
        return result.json()


    @staticmethod
    def file_upload(file: File):
        return CacheUploadPrerequisite(file.content, file.name)


    Settings = BoilerplateSettings
    Controller = BoilerplateController
    Model = BoilerplateModel