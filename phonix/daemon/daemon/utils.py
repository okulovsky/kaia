import requests
from pathlib import Path
from yo_fluq import FileIO
from avatar.server import AvatarApi


class ServerFileRetriever:
    def __init__(self, file_server_url: str):
        if not file_server_url.endswith('/'):
            file_server_url+='/'
        self.file_server_url = file_server_url

    def __call__(self, file_id):
        response = requests.get(f'http://{self.file_server_url}{file_id}')
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content


class FolderFileRetriever:
    def __init__(self, folder: Path):
        self.folder = folder

    def __call__(self, file_id):
        return FileIO.read_bytes(self.folder/file_id)


class AvatarFileRetriever:
    def __init__(self, api: AvatarApi):
        self.api = api

    def __call__(self, file_id: str):
        return self.api.file_cache.download(file_id)