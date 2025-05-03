from typing import List, Dict
import requests

from .controller import ChromaController
from .settings import ChromaSettings
from brainbox.framework import DockerWebServiceApi
from uuid import uuid4


class Chroma(DockerWebServiceApi[ChromaSettings, ChromaController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def get_relevant_context(self, query: str, n_samples: int = 5):
        response = requests.get(
            self.endpoint("/get_relevant_context"),
            params={
                "query": query,
                "n_samples": n_samples,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /get_relevant_context returned unexpected status code {response.status_code}\n{response.text}")
        return response.json()

    def download_model(self, embedding_model_name: str):
        response = requests.post(
            self.endpoint("/download_model"),
            data={
                "embedding_model_name": embedding_model_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /download_model returned unexpected status code {response.status_code}\n{response.text}")
        return response.json()

    def build_db_from_json(self, filename: str, collection_name: str):
        response = requests.post(
            self.endpoint("/build_db/from_json"),
            data={
                "filename": filename,
                "collection_name": collection_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /build_db/from_json returned unexpected status code {response.status_code}\n{response.text}")
        return response.json()

    def build_db_from_zip_archive(self, archive_name: str, collection_name: str):
        response = requests.post(
            self.endpoint("/build_db/from_zip_archive"),
            data={
                "archive_name": archive_name,
                "collection_name": collection_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /build_db/from_zip_archive returned unexpected status code {response.status_code}\n{response.text}")
        return response.json()

    def init_chroma_client(self, collection_name: str):
        response = requests.post(
            self.endpoint("/init_chroma_client"),
            data={
                "collection_name": collection_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /init_chroma_client returned unexpected status code {response.status_code}\n{response.text}")
        return response.json()

    def add_documents(self, data: List[Dict]):
        response = requests.post(
            self.endpoint("/add_documents"),
            data = {
                "data": data,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /add_documents returned unexpected status code {response.status_code}/{response.text}")
        return "OK"

    def delete_documents(self, ids: List[uuid4]):
        response = requests.post(
            self.endpoint("/delete_documents"),
            data = {
                "ids": ids,
            }
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /delete_documents returned unexpected status code {response.status_code}/{response.text}")
        return "OK"

    Settings = ChromaSettings
    Controller = ChromaController