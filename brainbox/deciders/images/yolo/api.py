import base64
from pathlib import Path
import requests
from ....framework import DockerWebServiceApi, FileLike
from .controller import YoloController
from .settings import YoloSettings

class Yolo(DockerWebServiceApi):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def analyze(self, file: FileLike.Type, model: str = None):
        loaded_model = self.get_loaded_model()
        if model is None:
            if loaded_model is None:
                raise ValueError("No model is provided and no model is preloaded")
        else:
            if loaded_model is None or loaded_model != model:
                self.load_model(model)

        with FileLike(file, self.cache_folder) as stream:
            data = base64.b64encode(stream.read()).decode("utf-8")
            response = requests.post(f"http://{self.address}/post_image", data={"image_base64": data})
        if response.status_code != 200:
            raise ValueError(response.text)
        response = requests.get(f"http://{self.address}/get_coordinates_faces")
        if response.status_code != 200:
            raise ValueError(response.text)
        return response.json()


    def load_model(self, model_id: str):
        reply = requests.post(
            f"http://{self.address}/load_model",
            json={
            "model_id": model_id,
        })
        if reply.status_code != 200:
            raise ValueError(reply.text)


    def get_loaded_model(self):
        reply = requests.get(f"http://{self.address}/get_loaded_model")
        return reply.json()['name']


    Controller = YoloController
    Settings = YoloSettings