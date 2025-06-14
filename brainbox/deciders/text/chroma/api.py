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

    def add_documents(self, data: List[Dict]):
        response = requests.post(
            self.endpoint("/add_documents"),
            json=data,
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /add_documents returned unexpected status code {response.status_code}/{response.text}")
        return "OK"

    def delete_documents(self, ids: List[uuid4]):
        response = requests.post(
            self.endpoint("/delete_documents"),
            json=ids,
        )
        if response.status_code != 200:
            raise ValueError(f"Endpoint /delete_documents returned unexpected status code {response.status_code}/{response.text}")
        return "OK"

    Settings = ChromaSettings
    Controller = ChromaController