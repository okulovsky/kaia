import base64
from pathlib import Path
import requests
from kaia.brainbox.core import IApiDecider, File



class VideoProcessor(IApiDecider):
    def __init__(self, address: str):
        self.address = address
        self._index = 0

    def processing_video(self, path_to_file: Path|str):
        response = requests.post(f"http://{self.address}/processing_video?file_name={path_to_file}")

        if response.status_code != 200:
            raise ValueError(response.text[:400])

        return response.json()

    def get_frames(self, batch_size: int = 100):
        result = []

        while True:
            response = requests.get(f"http://{self.address}/get_processed_frames?batch_size={batch_size}")
            if response.status_code != 200:
                self._index = 0
                raise ValueError(response.text)
            js = response.json()
            status = js.get("status")
            if status is not None and status == "All frames sent":
                self._index = 0
                break
            frames = js["frames"]
            task_id = self.current_job_id
            for image in frames:
                if image.startswith("data:image/png;base64,"):
                    image = image.split(",")[1]
                data = base64.b64decode(image)
                result.append(File(f'{task_id}.{self._index}.png', data, File.Kind.Image))
                self._index += 1

        return result