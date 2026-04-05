import os
from uuid import uuid4

from interface import IYolo, FileLike
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling_2 import FileLikeHandler, JSON


class YoloService(IYolo):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def analyze(self, image: FileLike, model: str | None = None) -> JSON:
        yolo_model = self.storage.get_model(model)
        fname = f'/resources/input_{uuid4()}.png'
        try:
            FileLikeHandler.write(image, fname)
            results = yolo_model(fname, stream=False)
            faces_coords = []
            for result in results:
                for box in result.boxes.xywh:
                    x, y, w, h = (
                        round(box[0].item()), round(box[1].item()),
                        round(box[2].item()), round(box[3].item()),
                    )
                    faces_coords.append({"x_center": x, "y_center": y, "w": w, "h": h})
            return {"objects": faces_coords}
        finally:
            if os.path.isfile(fname):
                os.unlink(fname)
