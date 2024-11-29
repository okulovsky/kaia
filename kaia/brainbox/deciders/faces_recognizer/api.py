from pathlib import Path
import requests
from kaia.brainbox.core import IApiDecider
from kaia.brainbox.deciders.arch.utils import FileLike


class FacesRecognizer(IApiDecider):
    def __init__(self, address: str):
        self.address = address

    def recognize_faces_from_image(self, path_to_file: Path|str):
        with FileLike(path_to_file, self.file_cache) as stream:
            data = stream.read()
            response = requests.get(f"http://{self.address}/from_image", data={"image_base64": data})

        if response.status_code != 200:
            raise ValueError(response.text)

        return response.json()

    def recognize_faces_from_video(self, path_to_file: Path|str):
        video_name = path_to_file.split('/')[-1]
        response = requests.get(f"http://{self.address}/from_video", params={"video_name": video_name})

        if response.status_code != 200:
            raise ValueError(response.text)

        return response.json()

class FacesRecognizerExtendedAPI(FacesRecognizer):
    def __init__(self, address: str):
        super().__init__(address)

    def load_model(self, repo_id: str, model_filename: str):
        reply = requests.post(
            f"http://{self.address}/load_model",
            json={
            "repo_id": repo_id,
            "model_filename": model_filename
        })
        if reply.status_code != 200:
            raise ValueError(reply.text)

    def get_loaded_model(self):
        reply = requests.get(f"http://{self.address}/get_loaded_model")
        return reply.json()