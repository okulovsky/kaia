import base64
import io
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download
from loguru import logger

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from ultralytics import YOLO

from validation_objects import LoadModelRequest
from validation_objects import CoordsFaceSquare
from PIL import Image
import traceback


class RecognizerApp:
    router = APIRouter()

    def __init__(self):
        self._similarity_threshold = 0.9
        self.model = None
        self.model_name = None
        self.data_directory = '/resources'
        self.models_directory = "/resources/models"
        self.hf_directory = '/resources/hf'
        os.makedirs(self.models_directory, exist_ok=True)
        os.makedirs(self.hf_directory, exist_ok=True)
        self.name_image_png = "image.png"

    def create_app(self):
        app = FastAPI()
        RecognizerApp.router.add_api_route("/", self.index, methods=["GET"])
        RecognizerApp.router.add_api_route("/post_image", self.post_image, methods=["POST"])
        RecognizerApp.router.add_api_route("/get_coordinates_faces", self.get_coordinates_faces, methods=["GET"])
        RecognizerApp.router.add_api_route("/load_model", self.load_model, methods=["POST"])
        RecognizerApp.router.add_api_route("/get_loaded_model", self.get_loaded_model, methods=["GET"])
        app.include_router(RecognizerApp.router)
        app.add_exception_handler(Exception, self.exception_handler)

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    async def exception_handler(self, request: Request, exc: Exception):
        tb = traceback.format_exc()
        return PlainTextResponse(
            content=f"An internal error occurred:\n\n{tb}",
            status_code=500,
        )

    def _model_id_to_path(self, model_id: str):
        repo_id, model_filename = model_id.split(':')
        return os.path.join(self.models_directory, repo_id, model_filename)

    def _download_model(self, model_id: str):
        repo_id, model_filename = model_id.split(':')
        path_to_cache_model = hf_hub_download(repo_id=repo_id, filename=model_filename, cache_dir=self.hf_directory)
        path = self._model_id_to_path(model_id)
        os.makedirs(Path(path).parent, exist_ok=True)
        shutil.copy(path_to_cache_model, self._model_id_to_path(model_id))


    def _load_model_internal(self, model_id: str):
        path = self._model_id_to_path(model_id)
        if not os.path.isfile(path):
            self._download_model(model_id)
        self.model = YOLO(path)
        self.model_name = model_id
        try:
            self.model.to("cuda")
        except:
            self.model.to("cpu")
        return "OK"

    async def load_model(self, request: LoadModelRequest):
        return self._load_model_internal(request.model_id)

    def get_loaded_model(self):
        return JSONResponse(content={"name": self.model_name})

    async def post_image(self, request: Request):
        await self._save_img_base64_to_png(request)
        return "OK"

    def get_coordinates_faces(self) -> dict[str,list]:
        source = f"{self.data_directory}/{self.name_image_png}"
        results = self.model(source, stream=False)
        faces_coords = self._format_result(results)

        return {"objects": faces_coords}

    def _format_result(self, results) -> list:
        faces_coords = []
        for result in results:
            for box in result.boxes.xywh:
                x_center, y_center, w, h = round(box[0].item()), round(box[1].item()), round(box[2].item()), round(box[3].item())
                faces_coords.append({
                    "x_center": x_center,
                    "y_center": y_center,
                    "w": w,
                    "h": h,
                })
        return faces_coords

    async def _save_img_base64_to_png(self, request: Request):
        form = await request.form()
        img_base64 = form["image_base64"]
        bytes_img = base64.b64decode(img_base64.replace("data:image/jpeg;base64,", "").strip())
        bytes_io = io.BytesIO(bytes_img)
        bytes_io.seek(0)
        img = Image.open(bytes_io)
        img.save(f"{self.data_directory}/{self.name_image_png}", "PNG")